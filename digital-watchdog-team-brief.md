# Digital Watchdog: Team Concept and Demo Brief

**Status:** Working concept for team discussion  
**Purpose:** Align on the problem, build a small demo in 1–2 hours, and explain the longer-term potential without claiming capabilities we have not built.

## 1. The idea in one sentence

A personal “digital watchdog” helps people notice when a call, message, or link falls outside their trusted context, pause before acting, verify through a known route, and find help if they have already acted.

The dog is a useful metaphor: it watches over a familiar space and alerts when something seems out of place. The product is software today. A physical companion or object is a possible future interface, not part of this demo.

## 2. The problem we are addressing

People are asked to judge whether a person, account, message, link, or website is trustworthy. That is getting harder because convincing signals can be copied or fabricated, and because the source itself may be compromised.

Examples raised by the team:

- A real person’s WhatsApp, Telegram, or community account may be compromised and used to share a malicious link. The familiar account creates trust even when the sender is no longer in control of it.
- Someone may impersonate a real person with generated or stolen images, video, voice, or profile details.
- A scammer may create a convincing website, brand, email address, or set of images. A polished appearance is not proof of legitimacy.
- Scams can arrive through unknown calls or texts, social media posts, job searches, and Marketplace conversations. The channel changes; the pressure and trust tactics can repeat.
- Scammers may imitate verification steps or official language, then use threats, authority, or urgency to discourage a person from checking independently.
- A person may click an anonymous link shared in a message or post without an easy way to know whether it is safe—or whether a familiar account has been compromised.
- Security checks later in the process may not tell a person whether the original request, link, recipient, or instructions were genuine. A later confirmation can still follow an earlier deception.
- What to do after clicking, sharing information, or sending money is often unclear. Prevention gets attention; recovery and practical next steps need to be part of the experience too.

**Core user problem:** “I can’t tell whether this contact or request is genuine, and I’m not sure what to do before or after I act.”

## 3. The solution hypothesis

Build an event-triggered assistant that protects a person’s **trusted perimeter**: the people, accounts, channels, and routines they rely on.

When an interaction looks unusual, the assistant should:

1. **Notice a mismatch.** For example, a familiar contact shares a new link with urgent payment instructions.
2. **Explain the uncertainty.** Say what is known and what is not. A familiar account may be compromised; a plausible image or caller claim does not prove identity.
3. **Offer a safe next step.** Suggest checking through a contact route the person already trusts, rather than replying to the suspicious message or using its link.
4. **Leave the choice with the person.** They can pause, verify, continue, or decline.
5. **Help after a mistake.** If they already clicked or shared information, give calm, ordered recovery guidance and point them to official channels.

This is not just a detector that labels content “real” or “fake.” It is a guide for deciding what to do when the source or context cannot be confidently verified.

## 4. What could make the idea distinctive

Many tools focus on whether a number, URL, or message has known scam signals. Our **differentiation hypothesis** is that this concept focuses on the relationship and context around the interaction:

- A known account is not automatically trusted if its behaviour or request is unusual.
- The assistant helps verify through a separate, known route instead of trusting the same message that raised concern.
- It supports the whole journey: before engagement, at the decision point, and after someone has acted.
- Its “watchdog” can be event-triggered and selective, rather than running a large AI model constantly.
- A familiar companion could make the experience feel approachable. Its image or voice is an interface cue, not proof of identity.

This is a promising framing, not a confirmed claim of market or technical novelty. We need to compare it with existing call-screening, link-checking, identity, and fraud-support tools before making a novelty claim to judges.

## 5. One- to two-hour demo: build this first

### Demo scenario

A message appears in a family or community chat from a familiar account. It contains an urgent request and a new payment or delivery link. The user cannot tell whether the account owner really sent it or whether the account was compromised.

This scenario demonstrates the central insight: **a familiar sender can still be an unsafe source for this particular request.**

### Smallest working experience

Create a single-page clickable software demo with four states:

1. **Incoming message:** Show the familiar contact, message, and link. Include a clear “Check this” action.
2. **Watchdog assessment:** Show a short summary such as: “This account is familiar, but this link and urgent request are unverified. The account could be compromised.” Show the specific visible clues; do not claim certainty.
3. **Decision:** Offer three choices: “Verify safely,” “Continue anyway,” and “Decline.” The recommended path should be to contact the person through a previously known number or another independent channel—not by replying to the same message.
4. **Already clicked:** Offer a calm next-step screen. For the demo, keep guidance general: stop entering information, use official contact routes for affected services, and seek help relevant to what was shared or paid. Do not imply that the prototype can reverse a payment or secure an account.

### Implementation boundary

- Use one scripted scenario and sample data; no real contacts, calls, or personal information.
- Use simple visible rules for the demo, such as an unfamiliar destination, an urgent request, or a request for payment or sensitive information. A real AI model is not required to demonstrate the concept.
- No actual call interception, background monitoring, hardware, account access, or claim that a link has been proven malicious.
- If an existing app scaffold is available, build the flow there. Otherwise, use the quickest tool the team already knows to create an interactive prototype.

### Suggested 90–120 minute run

| Time | Team activity | Output |
|---|---|---|
| 0–10 min | Agree on the scenario and exact demo boundary | One scenario; no extra features |
| 10–25 min | Sketch the four states and write the user-facing copy | Screen outline and risk explanation |
| 25–75 min | Build the clickable flow with scripted data and simple rules | Usable end-to-end demo |
| 75–95 min | Walk through the normal path and “already clicked” path; fix blockers | Demo that can be completed without explanation |
| 95–120 min | Prepare a short pitch and rehearse once | Clear problem, intervention, and future direction |

### Demo completion criteria

- A teammate can start at the incoming message and reach a safe verification choice without help.
- The demo distinguishes “familiar account” from “verified request.”
- The assessment explains its clues and uses uncertainty-aware language.
- The person can choose what happens next.
- The “already clicked” path gives a useful next step without promising recovery.
- The team can explain what is simulated and what is not built.

## 6. Longer-term story for judges

### Product direction: a personal trust perimeter

Over time, the assistant could become a user-controlled layer across calls, texts, messaging apps, links, and AI-agent interactions. It would compare a request with a person’s trusted contacts and expected routes, notice unusual changes, and help the person verify before acting.

The system should treat trust as contextual, not as a permanent green tick. A real account can be compromised; a real person can make an unusual request; a convincing image can be fake. The assistant should say what it can verify, what remains uncertain, and how to check independently.

### Selective, lower-compute approach

The long-term agentic story does not require a large model to inspect everything all the time:

- Run small, event-triggered checks when a user receives or shares a suspicious interaction.
- Use simple local rules for obvious signals and familiar context.
- Ask a more capable model for help only when the situation is ambiguous and the user chooses to inspect it.
- Keep sensitive data local where practical, minimise what is stored, and make permissions visible.

This is a design direction, not a measured compute result. Any compute or privacy claim needs testing.

### Verification and identity

A caller or agent saying “I am your bank” is not independent evidence. A future system could help connect people to verified accounts, official sources, or user-approved contact routes. Shared memories, family images, voices, or a familiar dog could make the interaction human and recognisable, but they can be copied or generated and should not be used alone to prove identity.

A future physical companion or household object could serve as a tangible interface or reminder. To provide actual proof, it would need a secure connection to a trusted identity or account. That is a research direction; we are not building or promising that hardware now.

### Agent and assistant interoperability

A useful long-term direction is to make the checking capability available to different assistants—potentially including phone assistants or ChatGPT-powered experiences—rather than making the concept depend on one brand. The demo does not integrate with Siri, ChatGPT, telcos, or messaging platforms. Access, permissions, and technical feasibility need to be explored separately.

### Call screening as an extension

A future call flow could let an assistant answer an unknown call, ask the caller to identify themselves and state the purpose, then give the user a concise summary and the choice to accept, decline, or verify independently. The caller’s answer is only a claim, not proof. Any call recording, transcription, data handling, or platform integration needs careful consent, privacy, and feasibility review.

### Malaysia context and responsible design

Before presenting regulatory compliance as a feature, research the relevant Malaysian privacy, telecommunications, consumer-protection, and scam-reporting requirements with current authoritative sources. In particular, do not treat a possible privacy-law issue as the same thing as a scam verdict. A caller may raise a privacy concern without being a scammer, and a scam may not announce itself through an obvious privacy violation.

The system should avoid diagnosing callers or claiming to know intent from “psychological” cues. It can surface observable pressure patterns—such as threats, urgency, secrecy, or requests for credentials—and explain why those patterns deserve a pause.

## 7. Short judge-facing pitch

“Scams are becoming harder to spot because trusted accounts can be compromised and fake identities, messages, and websites can look convincing. Most people are left to make the call themselves, often under pressure. We’re exploring a personal digital watchdog: an assistant that notices when a call, message, or link falls outside someone’s trusted context, explains the uncertainty, and helps them verify through a safer route. Our first demo focuses on one moment—a suspicious link from a familiar account—and shows support before and after a click. The longer-term vision is a selective, privacy-conscious trust layer that can work across channels and assistants.”

## 8. Open questions for the team

- Which user group should the first version serve: families, older adults, small businesses, or another group?
- What trusted context can the user provide without making setup burdensome or exposing sensitive information?
- Which independent verification route is practical in the first scenario?
- How should the assistant communicate uncertainty and avoid false reassurance or excessive alarms?
- What recovery guidance is useful for each type of action, and which official sources should support it?
- What existing products overlap with this idea, and where is the real gap?
- What phone, messaging, or assistant integrations are technically and legally feasible?

## 9. Guardrails for our claims

- Say “flags reasons to pause,” not “knows this is a scam,” unless we have evidence.
- Say “helps verify through a known route,” not “proves identity,” unless a real verification mechanism exists.
- Say “software demo,” not “hardware solution.”
- Say “future direction” for cross-platform agents, call interception, physical companions, and regulatory integration.
- Do not claim compliance, prevention rates, compute savings, or market novelty until researched and tested.
