# QodeFest — Digital Trust

## Problem Statement: When a Familiar Voice Can No Longer Be Trusted

_Event: QodeFest @ Alibaba Cloud Qwen Conference Malaysia 2026, 19 November 2026, 10:30am–4:30pm, Connexion Conference & Event Centre. Teams of four, randomly assigned. Building with Qoder and Qwen models._
_Track chosen: Digital Trust — strengthen digital safety, promote information integrity, and foster trust in the digital experience._
_Status: Problem only. No solution is decided in this document. The direction notes at the end are open questions from team discussion, not a chosen solution._

---

## The Person

Puan Salmah is 71 and lives alone in Petaling Jaya. She uses her phone mainly for WhatsApp calls with her children and family, and Google when she needs to search for something. She learned these slowly and is proud she can use them. She does not use many other apps, and she does not learn new ones quickly.

She is a fictional example, built from a real and common situation in Malaysia.

## Her Story — The Moment It Goes Wrong

One afternoon she gets a WhatsApp call. It sounds exactly like her son. He says he is in trouble, he has lost his phone, this is a new number, and he needs money transferred now. He asks her not to call his old number and not to tell anyone yet.

She can hear his voice. That used to be enough proof for her.

She is scared for him, so she does not think slowly. She opens her bank app and sends the money herself.

Later she learns it was not her son. The voice was copied with AI from a short video he had posted online. The money is gone.

## Why This Is a Malaysia Problem Now

- Malaysia has about 4.2 million people aged 60 and above, 12.3% of the population (DOSM, Current Population Estimates 2026). About 18.8% of senior citizens now live alone (National Health and Morbidity Survey 2025, as reported), so there is often no second person at home to check with.
- Senior citizens in Malaysia lost RM986.15 million across 3,837 scam cases in 2024 (PDRM figures, as reported).
- Malaysians overall lost close to RM2.97 billion to online scams in 2025. In most cases the victim is tricked into sending the money themselves, so normal bank security does not stop it.
- The AI version is already here. Bukit Aman Commercial Crime Investigation Department (CCID) said police were investigating 454 fraud cases believed to involve deepfake technology, with about RM2.72 million in losses (reported August 2024).
- CyberSecurity Malaysia has warned that cloned voices are used to impersonate family members, friends and colleagues to ask for urgent transfers, with voice samples taken from short public videos such as TikTok.
- A very short clip can be enough to copy a voice. Police have warned that even a few seconds of speech on a silent scam call can be recorded and used for AI voice cloning.
- Real cases in Malaysia follow the story above: a travel agent in Kuala Terengganu lost RM49,800 after a call in a voice that sounded like a close friend in urgent trouble; smaller losses were reported in Kuala Lumpur (RM3,000) and Penang (RM4,800) using the same method.
- Older adults in Malaysia mainly use smartphones for WhatsApp and Facebook to stay in touch with family, and many still face psychological, cognitive and physical barriers in learning new digital tools (Malaysian case study of older adults at Pusat Aktiviti Warga Emas centres, PLOS One, 2025).

## Why the Current Experience Fails Her

- **Voice and face were her proof, and they no longer work.** She cannot be expected to detect a deepfake by ear or by eye.
- **The help that exists is not in her moment.** She can call the National Scam Response Centre (NSRC) on 997 after it happens, or check an account number on PDRM's Semak Mule, or try to remember to hang up and call back — but all of that needs calm, memory and extra steps while she is panicking.
- **Urgency removes thinking time.** The scammer creates fear and a deadline on purpose, so advice she read before does not come back to her in time.
- **Sending the money looks normal to the bank.** She authorised it herself, under pressure. Recovery after a scam is low, so prevention before the transfer is what matters.
- **Fear has a second cost.** Even seniors who are never scammed lose confidence. They become afraid to use WhatsApp, online banking and new services at all, and fall further behind as everything moves online.

## The Problem in One Sentence

Older Malaysians who have only just learned basic phone tools now face AI calls that can fake a family member's voice and face, and in the panicked minute before they send money, they have no simple, trusted way to know if the person is real and if it is safe to act.

## What She Needs — A Need, Not a Solution

In that minute, she needs clarity and confidence:

- Without learning a new app.
- Without reading small text.
- Without remembering a long process.
- Without judging a fake voice or face herself.
- With a check that works under panic.
- With a check based on something a faraway scammer cannot fake.

## Question for the Team

How might we give a senior a clear and trusted check, in the moment of an urgent family call asking for money, before any money moves?

---

## Direction Notes From Discussion So Far — Open, Not Decided

These are the choices Frank made while thinking the problem through. They are working direction for the team to test, not a finished solution.

- **Track:** Digital Trust.
- **Person:** A family member / older person being scammed — not a business, not a young person.
- **Scary moment chosen:** A call or video that looks and sounds like a family member asking for money urgently.
- **What happens in that moment:** It looks and sounds like family, so the heart believes first. It is urgent, so there is no time to think slowly. It is about money and the safety of someone they love, so fear pushes them to act. The scammer usually adds secrecy: "don't tell anyone yet." Panic fills the mind and makes anyone forget steps.
- **Trust anchor — both together, not one alone:**
  - A secret word or question only the real family knows — something only the real family *knows*.
  - Something physical at home that only they hold — something only they *hold*.
  - A scammer on a call might fake one. Getting both is much harder.
  - Each has a weakness alone: a secret can be forgotten under panic, or tricked out of them; a physical thing can be lost, or used without really checking.
- **Hardware + software thinking:** Frank wants the team to think about a combination of hardware and software, even if the hardware is only a prototype. The instinct behind it: if everything on the screen can be faked, trust may need to live somewhere off the screen, in something physical a scammer cannot copy from far away.
- **Open question, still unanswered:** How do the secret word and the physical thing work together? Options raised in discussion:
  - The physical thing reminds them of the secret, so they do not have to remember it under panic.
  - Both must pass — the caller says the secret AND the physical check passes.
  - The physical thing is the main check, and the secret word is the backup.
  - The secret word is the main check, and the physical thing just keeps it safe at home.
- **Physical form, still unanswered:** One big button they press; a card they tap; a key-like object kept with house keys; or a small home device with a green / red light. The form must need no small text, no code to remember, and no steps in the right order while panicking.

## What the Technology Can and Cannot Do — Plain Words

For team members who have not used Qwen or Qoder before.

- **Qwen is the brain.** It can read and explain long letters, PDFs and rules step by step; see a photo of a form or a screenshot of a message, including the words inside it (the VL models); hear speech and turn it into text, and turn text back into speech; work across text, image, audio and video together (the Omni models); translate live; and work in many languages, which matters in Malaysia.
- **An agent** means it does not only answer once. It follows a small checklist itself: read this, check that, ask one question, produce a result, then check its own result.
- **Qoder is the building tool** powered by Qwen. It understands a whole project, plans, writes and tests code, and checks its own work. It has a coding mode for developers, and a general mode where a non-technical person describes the goal in plain language and it builds. The team has free Qoder credits and access to selected Qwen models in Alibaba Cloud Model Studio for this hackathon.
- **Honest limits for today:** Qwen and Qoder cannot connect to a real government or bank system in this hackathon, cannot prove a real person's identity for real, and will sometimes be wrong. A good demo does not claim "this is safe." It shows its source, shows its steps, and leaves the final yes to a human. All demo data should be fake.

## Frank's Role in the Team

Frank is non-technical. His useful roles in a team of four:

- Name one exact person and one painful minute, and keep the team on that one flow.
- Write the clear one-page instruction (the spec) that Qoder will build from.
- Test the build like a confused first-time user and say plainly where it breaks.
- Tell the 60-second story at the end: who, what moment, what went wrong before, what the check gives her.

Useful first questions for any new team: who can code, who has touched Qoder before, who is willing to present, and what time will we stop building to practise the demo?

## Sources

- DOSM, Current Population Estimates, Malaysia, 2026 — 4.2 million aged 60+, 12.3% of population.
- PDRM figures as reported in Malaysia, 2026 reporting — senior citizens lost RM986.15 million across 3,837 scam cases in 2024.
- Bank Negara Malaysia Annual Report 2025, as reported — Malaysians lost about RM2.8–2.97 billion to scams in 2025.
- Bukit Aman CCID, reported August 2024 — 454 fraud cases believed to involve deepfake technology, about RM2.72 million in losses.
- CyberSecurity Malaysia, as reported by Malay Mail — AI voice cloning impersonating family, friends and colleagues; voice cloned from short public videos.
- PLOS One (2025), "Intergenerational instructional strategies and elderly preferences for digital applications: A Malaysian case study" — older adults favour smartphones, WhatsApp and Facebook; digital literacy barriers persist.
- National Scam Response Centre (NSRC) hotline: 997. PDRM Semak Mule: semakmule.rmp.gov.my — checks bank accounts and phone numbers reported in fraud.

_Note: Figures above are as reported by the sources named. Where a figure comes from reporting of an official source rather than the official release itself, it is marked "as reported."_
