# How Do We Put It Live?

## Where does it go?

| Place name | Web address or area | What runs there? | Who owns it? |
|---|---|---|---|
| [WRITE HERE] | [URL OR REGION] | [WRITE HERE] | [NAME] |
| [WRITE HERE] | [URL OR REGION] | [WRITE HERE] | [NAME] |

## How do we put it live?

1. Open [LINK OR PATH].
2. Pick work line [BRANCH NAME].
3. Run `[COMMAND]`.
4. Wait for all checks.
5. Make sure each check says ✅.
6. Press [BUTTON OR COMMAND].
7. Open [LIVE ADDRESS].
8. Run the health checks below.
9. Tell [NAME] it is live.

## How do we undo a bad change?

If bad, do this.

1. Stop new changes.
2. Tell [NAME].
3. Open [LINK OR PATH].
4. Pick last good change [CHANGE ID].
5. Run `[COMMAND]`.
6. Wait for the old version.
7. Run the health checks again.
8. Write what failed in [LINK OR PATH].

## What settings and secret words are needed?

Never put secret values here.

| Setting name | Is it secret? | Where does it go? | Who can get it? |
|---|---|---|---|
| [SETTING NAME] | [YES / NO] | [WRITE HERE] | [NAME] |
| [SETTING NAME] | [YES / NO] | [WRITE HERE] | [NAME] |

## What automatic lines run?

Continuous integration and delivery (CI/CD) means automatic checks and delivery.

| Line name | What starts it? | What does it do? | What means pass? |
|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] |
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] |

## How do we know it is healthy?

| Check | How do we run it? | Good result | Bad result | Who gets told? |
|---|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [NAME] |
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [NAME] |

## What does a filled example look like?

> **Place:** Test area at test.shop.example.  
> **Put live:** Run `make deploy-test`.  
> **Undo:** Run `make undo-test`.  
> **Secret:** SHOP_KEY. Sam can get it.  
> **Healthy:** The status page says “okay.”
