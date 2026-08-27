-- 東京ぶらり旅プロジェクト
-- Supabase SQL Editorで1回実行してください。
-- Streamlit側はserver-side Secret / service_role相当のキーを使う前提です。

create extension if not exists pgcrypto;

create table if not exists public.burari_trips (
  id uuid primary key default gen_random_uuid(),
  trip_date date not null default current_date,
  destination text not null default '',
  status text not null default 'active' check (status in ('active','ready_for_diary','diary_done')),
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists burari_trips_trip_date_idx
  on public.burari_trips (trip_date desc);
create index if not exists burari_trips_status_idx
  on public.burari_trips (status, started_at desc);

create table if not exists public.burari_photos (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.burari_trips(id) on delete cascade,
  storage_path text not null unique,
  captured_at timestamptz not null default now(),
  reflection_json jsonb not null default '{}'::jsonb,
  signals_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists burari_photos_trip_idx
  on public.burari_photos (trip_id, captured_at);

create table if not exists public.burari_diaries (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null unique references public.burari_trips(id) on delete cascade,
  title text not null default '',
  diary_text text not null,
  raw_conversation jsonb not null default '{}'::jsonb,
  ai_meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists burari_diaries_created_idx
  on public.burari_diaries (created_at desc);

create table if not exists public.burari_monthly_reviews (
  id uuid primary key default gen_random_uuid(),
  review_month date not null unique,
  review_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 写真はprivate bucketに保存します。
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'burari-photos',
  'burari-photos',
  false,
  8388608,
  array['image/jpeg','image/png','image/webp']
)
on conflict (id) do update set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

-- ブラウザへSupabaseキーを渡さず、Streamlitサーバーからservice_role相当でアクセスします。
alter table public.burari_trips enable row level security;
alter table public.burari_photos enable row level security;
alter table public.burari_diaries enable row level security;
alter table public.burari_monthly_reviews enable row level security;

grant all on table public.burari_trips to service_role;
grant all on table public.burari_photos to service_role;
grant all on table public.burari_diaries to service_role;
grant all on table public.burari_monthly_reviews to service_role;
