# Tutorial: parola și Git, pas cu pas (cu verificări)

Fiecare pas are o **Verificare**. Dacă verificarea nu iese cum scrie, oprește-te și nu continua.
Rulezi totul în PowerShell, din folderul proiectului:

```
cd "C:\Users\mihai\Desktop\Call of Duty Scoreboard\cod-scoreboard"
```

---

## Partea 1. Schimbi parola MySQL

Parola veche a stat scrisă în scripturile tale vechi, deci o consideri expusă.

**1.1 Schimbi parola**
```
$mysql = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
& $mysql -uroot -p -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'PAROLA_NOUA_AICI';"
```
- Te întreabă parola veche (`-p`), o scrii.
- Înlocuiește `PAROLA_NOUA_AICI` cu parola nouă. Păstrează ghilimelele simple.
- Folosește o parolă lungă, fără ghilimele simple (`'`) în ea.

**Verificare:** rulează `& $mysql -uroot -p -e "SELECT 1"` și scrie parola NOUĂ. Trebuie să afișeze `1`. Parola veche trebuie să dea `Access denied`.

**1.2 Actualizezi `.env`**
```
notepad .env
```
Schimbi doar linia `MYSQL_ROOT_PASSWORD=` cu parola nouă. Restul rămâne (`MYSQL_DATABASE=cod_dev`, `MYSQL_HOST_PORT=3306`). Salvezi.

**Verificare:**
```
$env:PYTHONPATH = "src"
py -m pytest -q
```
Trebuie `30 passed`. Dacă vezi `Access denied`, parola din `.env` nu e cea nouă.

**1.3 Scripturile vechi**
Scripturile vechi (`game.py`, `seed_player.py` etc.) sunt în folderul de deasupra, NU în `cod-scoreboard`. Repo-ul pe care îl urci pe GitHub e doar `cod-scoreboard`, deci ele nu ajung pe GitHub.
Nu le mai rula: generatorul nou le înlocuiește. Au parola veche, care oricum nu mai merge. Dacă vrei să le păstrezi, șterge parola din ele sau lasă-le pe loc, în afara repo-ului.

---

## Partea 2. Git, de la zero până pe GitHub

**2.1 Verifici că ai Git**
```
git --version
```
Dacă zice că nu există comanda, instalează „Git for Windows" de pe git-scm.com, închide și redeschide PowerShell, apoi reia.

**2.2 Îți setezi numele (o singură dată pe calculator)**
```
git config --global user.name "Mihai Tatu"
git config --global user.email "emailul-contului-tau-de-github"
```
Verificare: `git config --global --list` arată cele două valori.

**2.3 Creezi repo-ul local**
```
git init -b main
```
**Verificare:** apare un folder ascuns `.git` (`ls -Force`) și mesajul `Initialized empty Git repository`.

**2.4 Verifici ce ar intra în repo, ÎNAINTE de `add`**
```
git status
```
Sub „Untracked files" trebuie să vezi: `.github/`, `docs/`, `sql/`, `src/`, `tests/`, `.env.example`, `.gitignore`, `README.md`, `docker-compose.yml`, `pytest.ini`, `requirements.txt`, `ruff.toml`.

**Trebuie să NU apară:** `.env`, `.venv`, `__pycache__`, `.pytest_cache`.
Dacă vezi `.env` în listă, **oprește-te**: `.gitignore` nu l-a prins și parola ar ajunge pe GitHub. Spune-mi.

**2.5 Adaugi și faci primul commit**
```
git add .
git status
```
A doua oară `git status` arată „Changes to be committed". Verifică iar că `.env` nu e acolo. Apoi:
```
git commit -m "Initial commit: generator, schema, tests"
```
**Verificare:** `git log --oneline` arată un singur commit.

**2.6 Verifici că nu a intrat nicio parolă în cod**
```
git grep -n -i "password"
```
Trebuie să vezi doar nume de variabile (`MYSQL_ROOT_PASSWORD`, `os.getenv(...)`) și texte din documentație. NU trebuie să vezi o valoare reală de parolă. Dacă vezi una, spune-mi înainte să faci push.

**2.7 Creezi repo-ul pe GitHub**
- Intri pe github.com, cont `thetatu13`, „New repository".
- Nume: `cod-scoreboard`.
- Public sau Private (alegi tu; Public e mai bun pentru portofoliu).
- **Nu bifa** „Add a README", „.gitignore" sau licență. Trebuie să rămână gol.

**2.8 Legi local de GitHub și faci push**
```
git remote add origin https://github.com/thetatu13/cod-scoreboard.git
git push -u origin main
```
La prima rulare se deschide o fereastră de autentificare GitHub. Te loghezi în browser și confirmi.

**Verificare:** pe pagina repo-ului de pe GitHub vezi folderele `src`, `tests`, `docs`, `sql`. Intră în repo și verifică că NU există fișierul `.env`.

---

## Dacă greșești

| Problemă | Ce faci |
|---|---|
| `.env` a ajuns în `git status` înainte de commit | Nu da commit. Spune-mi. |
| Ai dat deja commit cu `.env`, dar încă NU ai dat push | `git rm --cached .env`, apoi `git commit --amend`. Schimbi și parola. |
| Ai dat push cu `.env` pe GitHub | Schimbă IMEDIAT parola MySQL. Ștergerea fișierului nu ajunge, parola rămâne în istoric. |
| `git push` zice „remote origin already exists" | `git remote remove origin`, apoi reiei `git remote add ...` |
| `git push` zice „rejected" sau „non-fast-forward" | Ai bifat README când ai creat repo-ul. Spune-mi, nu forța push-ul. |

## Regula de la care nu abatem

Un fișier cu parole nu intră în Git niciodată. Parolele stau doar în `.env`, iar `.env` e în `.gitignore`.
