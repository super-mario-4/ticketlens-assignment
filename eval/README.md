# Classification evaluation

`labels.csv` is the reference set, `report.md` the latest quality result and `bench.md` the latest speed result.

## Who labelled the tickets

**The AI coding agent wrote these labels, not the author.** The assignment asks for tickets "you labelled yourself", and PRD section 9 and TRD section 12 say the same. The author asked the agent to carry out this step, so the file is a first version: **the author must review and correct it, then run `make eval` again, before the result is presented as their own labelling.**

What keeps the labels honest:

- They were written from the masked text and the rules in PRD section 7, before any model answer for these tickets was seen.
- The hash of the 111 scored labels was recorded before the first evaluation run, and they were not changed after the results were read.
- One exception, which affects no score: the real complaints of the 8 injection tickets were chosen before the first run, but the command that wrote them failed. They reached the file after that run, with the values chosen earlier. They are used only in the injection table.
- A label the rules do not settle is marked `ambiguous = yes`, and the report gives figures with and without those tickets.

Limits:

- One labeller, with no second opinion and no repeat labelling.
- The same family of model wrote the prompt rules and the labels, so shared blind spots are possible.
- The dataset is built from a small number of message templates. A high score here says little about real messages. Results apply to this set only (TRD section 12).

## Prompt versions

`report-prompt-v1.md` is the first run, with no knowledge of the results. Priority accuracy missed its target there, so prompt `v2` added the priority examples from the PRD section 7 table, which `v1` had left out. `report.md` is the `v2` run.

**The `v2` figures come from a set the agent had already seen, so they are not independent.** The change uses PRD text only and was not fitted to single tickets, but only a fresh set can show whether it holds on new tickets. The `v1` file predates the injection labels, so its injection table is corrected by hand, as the note at its top says.

## The set

| Group | Tickets | Use |
| --- | --- | --- |
| `expected = model` | 111 | Sent to the model and scored |
| `expected = no_content` | 7 | Must be held at import |
| `expected = injection_suspected` | 8 | Must be held at import, then sent straight to the model to test the prompt alone |

The tickets are unique texts from a seeded sample of `data/tickets.csv`, with extra picks for rare categories. They cover all 12 categories, all 4 priorities and 5 language groups. Language means the main writing of the message: `uz_latin`, `uz_cyrillic`, `ru`, `ru_latin` and `mixed`, which is a message that combines them.

Labelling rules beyond PRD section 7, for cases it leaves open. These are the ones marked `ambiguous`:

- A question about why a commission was charged is `fees_charges`, `Low`: it asks for information.
- A card declined in a shop with no money taken is `card_issues`, `Medium`.
- An expired card is `card_issues`, `Medium`: it blocks use of the card.
- A late fee despite paying on time is `credit_installments`, `High`.
- A rude operator is `support_complaints`, `Low`. No reply from support for two days is `Medium`.

## Running it

With the stack up and `data/tickets.csv` imported:

```bash
docker compose stop worker   # The model cannot serve both without slowing down.
make eval                    # Calls the model once per ticket. Writes nothing to the database.
docker compose start worker
make bench                   # Reads stored results. Needs no model.
```
