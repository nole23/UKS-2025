# UKS-2025
Repository otvoren za potrebe studentskog projekta – simulacija jednostavne Docker Hub platforme.

---

## Osnovne smernice razvoja
- Kompletan razvoj se radi na **feature/*** granama.
- Push ka **develop** ili **master** granama nije direktno dozvoljen; koristi PR (Pull Request) workflow.
- PR ka **develop** grani koristi **hci.yml** workflow za build i testiranje client i server delova.
- PR merge u **master** pokreće **ci.yml** workflow i finalni Docker build.

---

## Baza podataka
- Projekat koristi **PostgreSQL** u produkciji, dok testovi rade na **SQLite** za lakše lokalno testiranje.

---

## Docker i servisi
- Servisi se pokreću koristeći `docker-compose.yml`.
- Nepotrebni fajlovi (`node_modules`, `.pyc`, debug printovi) nisu uključeni u produkcioni Docker image.

### Build i pokretanje svih servisa
```bash
docker-compose up --build
```

## Pristup aplikaciji
- Angular client: http://localhost
- Django API: http://localhost/api/

## Pokretanje testova
```bash
docker-compose run web python manage.py test
```

## Workflow PR / CI
1. Razvoj se radi na feature/* granama.
2. PR ka develop za CR/CI:
   - hci.yml workflow build-a i testira client i server.
3. Merge u master:
   - Pokreće ci.yml workflow i finalni Docker build.

## Struktura repositorijuma
* uks-server/       # Django backend
* uks-client/       # Angular frontend
* uks-nginx/        # Nginx reverse proxy za client i API
* docker-compose.yml
* ci.yml            # CI workflow za master
* hci.yml           # CI workflow za develop
* README.md
