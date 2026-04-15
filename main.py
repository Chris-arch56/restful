from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import uuid
import os

app = FastAPI(title="Movies REST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "posters"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def home():
    return {"message": "Movies API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/movies")
def get_movies():
    response = supabase.table("movies").select("*").order("id").execute()
    return response.data


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    response = supabase.table("movies").select("*").eq("id", movie_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Movie not found")

    return response.data[0]


@app.post("/movies")
async def add_movie(
    title: str = Form(...),
    director: str = Form(...),
    genre: str = Form(...),
    description: str = Form(...),
    poster: UploadFile = File(...)
):
    try:
        file_extension = poster.filename.split(".")[-1] if "." in poster.filename else "jpg"
        file_name = f"{uuid.uuid4()}.{file_extension}"
        file_bytes = await poster.read()

        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": poster.content_type}
        )

        poster_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)

        new_movie = {
            "title": title,
            "director": director,
            "genre": genre,
            "description": description,
            "poster_url": poster_url
        }

        response = supabase.table("movies").insert(new_movie).execute()
        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/movies/{movie_id}")
def update_movie(
    movie_id: int,
    title: str = Form(None),
    director: str = Form(None),
    genre: str = Form(None),
    description: str = Form(None)
):
    update_data = {}

    if title is not None:
        update_data["title"] = title
    if director is not None:
        update_data["director"] = director
    if genre is not None:
        update_data["genre"] = genre
    if description is not None:
        update_data["description"] = description

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    response = supabase.table("movies").update(update_data).eq("id", movie_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Movie not found")

    return response.data


@app.put("/movies/{movie_id}")
def replace_movie(
    movie_id: int,
    title: str = Form(...),
    director: str = Form(...),
    genre: str = Form(...),
    description: str = Form(...)
):
    replacement_data = {
        "title": title,
        "director": director,
        "genre": genre,
        "description": description
    }

    response = supabase.table("movies").update(replacement_data).eq("id", movie_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Movie not found")

    return response.data


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    check = supabase.table("movies").select("*").eq("id", movie_id).execute()

    if not check.data:
        raise HTTPException(status_code=404, detail="Movie not found")

    response = supabase.table("movies").delete().eq("id", movie_id).execute()
    return {"message": "Movie deleted", "deleted": response.data}