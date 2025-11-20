# Pitcher Game Log Column Glossary

| Column | Meaning | Typical Values |
|---|---|---|
| Rk | Row index in table | integer 1..n |
| Gcar | Career game number | integer |
| Gtm | Team game number this season | integer |
| Date | Game date | YYYY-MM-DD |
| Team | Team abbreviation | 'ARI','NYY', etc |
| Unnamed: 5 | Home/away marker | empty or '@' |
| Opp | Opponent team | three-letter code |
| Result | game final + score | "W, 7-3" etc |
| Inngs | Game Score leverage inning code | GS-7 etc |
| Dec | Pitcher decision | W(3-0), L(2-1), blank |
| DR | Decision rank / pitcher role code | integer-ish |
| IP | Innings pitched (baseball tenths) | e.g. 6.2 means 6 + 2/3 |
| H | Hits allowed | integer |
| R | Runs allowed | integer |
| ER | Earned runs allowed | integer |
| HR | Home runs allowed | integer |
| BB | Walks (BB) issued | integer |
| IBB | Intentional walks | integer |
| SO | Strikeouts | integer |
| HBP | Hit by pitch | integer |
| BK | Balks | integer |
| WP | Wild pitches | integer |
| BF | Batters faced | integer |
| ERA | ERA after this game | float |
| FIP | FIP after this game | float |
| Pit | Pitch count | integer |
| Str | Strikes thrown | integer |
| StL | Strikeouts looking? | small int |
| StS | Strikeouts swinging? | small int |
| GB | Ground balls allowed | small int |
| FB | Fly balls allowed | small int |
| LD | Line drives allowed | small int |
| PU | Popups allowed | small int |
| Unk | Unclassified BIP | small int |
| GmSc | Game Score metric | float-ish |
| SB | Stolen bases allowed | int |
| CS | Caught stealing | int |
| PO | Pickoffs | int |
| AB | At-bats faced | int |
| 2B | Doubles allowed | int |
| 3B | Triples allowed | int |
| GIDP | Ground into double play | int |
| SF | Sacrifice flies | int |
| ROE | Reached on error | int |
| BAbip | BABIP allowed | float |
| aLI | average Leverage Index | float |
| WPA | Win Probability Added | float |
| acLI | context adjust LI | float |
| cWPA | clutch WPA style | float (often %) |
| RE24 | run expectancy change | float |
| DFS(DK) | DraftKings fantasy pts | float |
| DFS(FD) | FanDuel fantasy pts | float |
| Entered | run-value context when entered | text |
| Exited | run-value context when exited | text |
