create table if not exists movies (
    id bigint generated always as identity primary key,
    title text not null,
    director text not null,
    genre text not null,
    description text not null,
    poster_url text,
    created_at timestamp with time zone default now()
);

alter table movies enable row level security;

create policy "public read movies"
on movies
for select
to public
using (true);

create policy "public insert movies"
on movies
for insert
to public
with check (true);

create policy "public update movies"
on movies
for update
to public
using (true);

create policy "public delete movies"
on movies
for delete
to public
using (true);

insert into storage.buckets (id, name, public)
values ('posters', 'posters', true)
on conflict (id) do nothing;

create policy "public view posters"
on storage.objects
for select
to public
using (bucket_id = 'posters');

create policy "public upload posters"
on storage.objects
for insert
to public
with check (bucket_id = 'posters');

create policy "public delete posters"
on storage.objects
for delete
to public
using (bucket_id = 'posters');