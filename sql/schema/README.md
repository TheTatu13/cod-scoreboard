# sql/schema

Pune aici schema exportată din baza ta (fără date), ex. `01_schema.sql`.
Docker o rulează automat la prima pornire a containerului (volum gol).

Export (Git Bash, din rădăcina repo-ului):

    mysqldump -u root -p --no-data --routines cod_scoreboard > sql/schema/01_schema.sql

Dacă modifici schema după prima pornire: `docker compose down -v && docker compose up -d`
(`-v` șterge volumul, deci și datele; ele se regenerează din generator + seed).
