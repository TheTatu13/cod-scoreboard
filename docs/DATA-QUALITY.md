# Calitatea datelor: generatorul ca sistem-sursă

Datele sunt sintetice. Setul static, mic și curat e un semnal slab la angajatori; un generator
care se comportă ca un sistem real, cu erori controlate, e un avantaj. Din săptămâna 3,
generatorul produce zilnic o partiție nouă și poate injecta defecte, cu rate configurabile
într-un fișier YAML versionat (`chaos.yml`).

## Defecte injectate (plan)

| Defect | Cum îl injectezi | Unde îl prinzi | Ce se întâmplă cu el |
|---|---|---|---|
| kill duplicat | repetă un `kill_id` cu o rată `p` | test `unique` în dbt + verificare la ingestie | păstrezi un singur rând, numeri duplicatele |
| eveniment întârziat | un kill dintr-un meci de ieri, livrat azi | ingestie incrementală (watermark) | încărcat în partiția corectă, marcat `late` |
| `victim_id` orfan | ID de jucător inexistent | test `relationships` | carantină în `rejected_kill_event` |
| `killer_id = victim_id` | decide tu dacă e invalid în regulile tale | test custom | carantină sau accept (decizie documentată) |
| timestamp în afara meciului | `timestamp_in_match` > `duration_sec` | test custom | carantină |
| nume de armă murdar | majuscule sau spații în plus | staging (normalizare) | corectat, numărat |
| câmp lipsă | `NULL` unde nu e permis | `not_null` | carantină |
| schema drift | în ziua X apare un câmp nou sau o coloană redenumită | verificare de schemă la ingestie | alertă + încărcare cu mapare explicită |

## Reconciliere zilnică

Pentru fiecare zi: `rânduri citite = rânduri încărcate + rânduri respinse`.
O diferență nejustificată face rularea să eșueze și să trimită alertă. Raportul se salvează
în baza de date, ca să poți desena „% respinse pe zi, pe tip de eroare" în dashboard.

## Determinism

Același `--seed` și aceeași `--date` produc exact aceleași date și aceleași defecte. Asta face
testele reproductibile și e un argument bun la interviu.

## Onestitate în README

Scrie explicit: datele sunt sintetice, erorile sunt injectate controlat și nu estimează
realitatea. Avantajul real: ai „ground truth" (știi ce defecte ai pus), deci poți demonstra
că pipeline-ul le prinde, lucru pe care datele reale nu ți-l dau.
