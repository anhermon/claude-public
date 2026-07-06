# Django + DRF Conventions

Use when the project needs a built-in admin panel, complex ORM relationships, or follows an ORM-first design.

## Stack

| Concern | Tool |
|---|---|
| Framework | Django + Django REST Framework |
| Serialization | DRF serializers or drf-spectacular for OpenAPI |
| Auth | `djangorestframework-simplejwt` or `django-allauth` |
| ORM | Django ORM (sync); `django-ninja` if async routes are needed |
| Environment | `django-environ` or `pydantic-settings` |

## Key conventions

- Settings split: `settings/base.py`, `settings/development.py`, `settings/production.py`. Never use `settings.py` at root for production.
- Custom User model from day one — never add it after initial migration.
- Use `select_related` / `prefetch_related` to prevent N+1 queries.
- DRF viewsets over function-based views for CRUD resources.
