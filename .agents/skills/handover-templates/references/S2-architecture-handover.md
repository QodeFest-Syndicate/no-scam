# How Does It All Fit Together?

## What is the big picture?

**Main parts:**

- [PART NAME]: [WRITE WHAT IT DOES]
- [PART NAME]: [WRITE WHAT IT DOES]
- [PART NAME]: [WRITE WHAT IT DOES]

**Draw the flow:**

```text
[USER OR THING]
       |
       v
[PART ONE] ---> [PART TWO]
       |
       v
[DATA STORE]
```

## What talks to what?

| Thing A | Goes to Thing B | What do they send? | How often? |
|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] |
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] |

## Where does data live?

| Place name | What is inside? | How big? | Who reads it? | Who changes it? |
|---|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [SIZE] | [NAME] | [NAME] |
| [WRITE HERE] | [WRITE HERE] | [SIZE] | [NAME] | [NAME] |

## What are the rules for talking?

An application programming interface (API) lets apps talk.

| Door or address | What goes in? | What comes out? | What if it fails? |
|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] |
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [WRITE HERE] |

## How do we test this is right?

| What do we check? | How do we check it? | What means pass? | Who checks? |
|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [NAME] |
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [NAME] |

## What could go wrong?

| Bad thing | How likely? | How bad? | What stops it? |
|---|---|---|---|
| [WRITE HERE] | [LOW / MEDIUM / HIGH] | [LOW / MEDIUM / HIGH] | [WRITE HERE] |
| [WRITE HERE] | [LOW / MEDIUM / HIGH] | [LOW / MEDIUM / HIGH] | [WRITE HERE] |

## What did we choose and why?

| What did we choose? | What did we not choose? | Why? | Who agreed? |
|---|---|---|---|
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [NAME] |
| [WRITE HERE] | [WRITE HERE] | [WRITE HERE] | [NAME] |

## What does a filled example look like?

> **Main parts:** Web page, order worker, order list.  
> **Flow:** Buyer → web page → order worker → order list.  
> **Talking rule:** Send item name and count.  
> **Pass check:** A saved order has the same count.  
> **Risk:** The order list may stop. Try again twice.
