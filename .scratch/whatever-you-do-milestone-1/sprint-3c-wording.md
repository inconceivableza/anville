# Sprint 3c wording sheet

The exact participant-facing wording for sprint 3c, settled 26 Oct from the content owner's feedback of 23–25 Oct. Apply it as written; don't reword. Where a row says "remove", remove the text and anything that only exists to show it.

`{name}`, `{count}`, `{min}` and the like are the template's or pathway's existing placeholders.

## Everywhere

| Now | New |
|---|---|
| strengths assessment, Strengths Assessment, the assessment | strengths evaluation (lower case mid-sentence; "Strengths evaluation" at the start of a line or as a title) |
| self-assessment | strengths evaluation |
| an observer's "assessment" (what they send) | evaluation |
| workbook (the course as a whole) | journey |

These apply to participants, observers, coaches and the homepage. Code names stay as they are: ids, block types, function names. Copy that a test checks changes with the test.

## Homepage

### Top of the page
- Remove every link in the top bar (Home, How it works, The assessment, Impact, Coaches, Begin). The logo stays.
- Hero summary. Now: "A guided workbook for discerning your calling through scripture, a strengths assessment, feedback from people you trust, and a coach. For adults aged 18 and over." New: **"A guided journey for discerning your calling through scripture, a strengths evaluation, feedback from people you trust, and a coach."**
- Remove the "For coaches" button. Keep "Begin your journey".
- Add, below the buttons: **"Learn more"**, with a down arrow, leading to the overview.

### Overview
- Heading stays: "Whatever You Do is a pathway for discerning your purpose."
- Pillars: Scripture · Strengths evaluation · Peer feedback · Coach oversight · Journey
- Sign line. Now: "A calling workbook for every season of life". New: **"A calling journey for every season of life"**
- Add after the pillars: **"Along the way, you'll come to understand your God-given gifts, talents and limitations, explore what the Bible teaches about work and calling, and find practical next steps. At the start and the end, you answer the same questions, so you can see what has changed."**
- Add a **"Begin your journey"** button.

### How it works
- Remove "Five steps to help you reflect on your gifts, hear from people who know you, and explore what comes next."
- Each step keeps its title and loses its bullets and its "In your workbook" box. The summary becomes:

| Step | Title | Summary |
|---|---|---|
| 01 | **Discover your gifts and talents** | Reflect on your strengths through a guided evaluation and scripture: sort 36 statements about yourself, and explore the gifts described in Romans 12 and 1 Corinthians 12. |
| 02 | Hear from people who know you | Invite at least three people you trust to share their perspective, then compare it with your own and notice where your views align or differ. |
| 03 | Make sense of your story | Work through guided prompts on your life, your work and the moments that have shaped you, at your own pace, and notice the themes that run through them. |
| 04 | Explore a sense of calling | Draw together your gifts, experience and reflections, put your sense of calling into words, and identify practical next steps. |
| 05 | Return to what you discovered | Write a letter to your future self, capturing what matters to you now and the steps you want to take, to revisit later. |

- The section's label. Now: "How the assessment works". New: **"How it works"**

### Space to reflect
- Remove the section. Its text now lives in the overview.

### The difference it makes (new, before the churches section)
Take it from the hackathon v3 prototype (`Prototypes for reference/whatever-you-do-site-hackethon-artifact-v3/index.html`, "The difference it makes"):
- Heading: **"The difference it makes"**
- **71%** had a more detailed understanding of their God-given gifts, talents and limitations
- **86%** had a more detailed understanding of what the Bible teaches about work and calling
- **100%** had a clearer practical plan for how to pursue God's purpose for their life

### For churches
- Label stays: "For churches"
- Heading. Now: "Equip people to see their everyday work as part of their calling." New: **"Releasing and equipping your members to do whatever they do for the glory of God."**
- Lede. Now: "Whatever You Do can be used by individuals and by churches supporting people as they reflect on gifts, work and purpose." New: **"Most church members spend 95% of their week outside the church building. Whatever You Do equips them to see that everyday work as ministry."** (with "95%" in bold)
- Points. Replace all three:
  - **Run it together:** Take your congregation, small group or staff team through it as a course.
  - **Raise up coaches:** Equip wise people in your church to walk alongside others, with a short briefing pack.
  - **Free for participants:** No cost to the people you send through it.
- Button: **"Join the waitlist"**, leading to "Stay in touch".

### Articles ("Ideas to explore")
- Remove the section.

### Testimonial
- Label. Now: "A story from a parent". New: **"Impact"**
- The quote's words and caption stay. Its text size comes down to hackathon v3's ("A story from a parent" section), all at one size.

### Stay in touch (one email field: newsletter, contact and the churches waitlist)
From hackathon v3's "Stay in touch", with its line widened to cover the waitlist:
- Heading: **"Stay in touch"**
- Line: **"Thoughtful writing on vocation, faith and work, and news of Whatever You Do for churches, delivered occasionally."**
- Field label (for screen readers): "Email address". Placeholder: "Your email"
- Button: **"Subscribe"**
- Under the form: **"We'll only use your email to send these updates, and you can unsubscribe at any time. See our privacy notice."** ("privacy notice" links to the privacy page)
- After subscribing: **"Thanks, you're subscribed. Look out for our next note."**, shown in place of the form on the homepage, with no new page
- "Join the waitlist" and "Contact us" jump down the homepage to this form

### Footer, green part
- Heading stays: "Everyone has a purpose. Do you know yours?"
- The five calling boxes become images (from hackathon v3's calling photos), each captioned with its calling and line as now. Nothing about donations.
- "Begin your journey" stays.

### Footer, black part
- Left: the logo, and under it, replacing "A guided calling workbook": **"“Whatever you do, work at it with all your heart, as working for the Lord.” Colossians 3:23 (NIV)"**
- Right, one column of links: **How it works · Impact · For churches · Contact us** ("Contact us" leads to "Stay in touch") · **Privacy**
- Remove the "Note" column, "The assessment" and "Writing".
- "© 2026 Whatever You Do" and "Credits" stay.

## Onboarding

### Consent (moves into the onboarding steps)
- One tick box, required to continue: **"I agree to Whatever You Do storing my answers, including anything about my faith, work or health, as set out in the privacy notice."**
- Beside it, a box that opens to the details, headed **"What this means"**. It holds today's consent text with these changes:
  - "What is stored" stays as it is.
  - "Who sees what": remove the group admins paragraph. In the coach paragraph, "self-assessment results" becomes "strengths evaluation results".
  - "Your choice": remove ", and your enrolment code, if you were given one, does not agree for you". In the withdrawal sentence, remove "you stay in any groups you have joined, but their admins see only your first name and that you have not consented".
  - The "Draft wording" notice stays until the privacy page is signed off.
- The consent page (for reviewing or withdrawing later) shows the same text.

### Messages
- The words of "Choose what's bringing you to the course to continue." and "Answer all five to continue" stay. They now show only after Continue is pressed.
- Remove the "Saved" note after each answer to the five questions.

## Hub

| Where | Now | New |
|---|---|---|
| Next step, Section 1 | Take the ten-minute strengths assessment and read three short passages on gifts. | **Start with the ten-minute strengths evaluation.** |
| Section 1's lock note on its parts | Opens from {title}, once you've read the passages. | **Opens from {title}.** |
| Coach card, bold | Section 3 opens once your coach accepts | **A coach helps you test what you're discovering with someone who knows you and your faith.** |
| Coach card, normal | When you're ready, ask someone to walk this with you. | **You'll need one before the later sections open.** |
| Coach card button | Manage | **Choose your coach**; once one is chosen, **See your coach** |
| Five trusted voices card | Invite people who know you well. Their answers sit beside your own in Section 1, combined so you never see whose is whose. | Invite people who know you well. Their answers sit beside your own **strengths evaluation**, combined so you never see whose is whose. |
| Five trusted voices button | Manage | **Invite people** |
| Below the sections | Your groups | Remove |

### Six sections
Section 1 splits into two numbered sections, so the course has six:

| No. | Title |
|---|---|
| 01 | **How you've been designed – your strengths** |
| 02 | **How others see you** |
| 03 | The shape of your life |
| 04 | Putting your calling into words |
| 05 | Growth plan |
| 06 | A letter to your future self |

- Hub count. Now: "{complete} of {total} sections complete", where the total includes parts and side cards. New: the same words, counting the six numbered sections only.
- Every "Section N" a participant sees follows the new numbers: lock notes, "Download Section N (PDF)", "I've finished Section N", the "Waiting on answers" line.

## Sections 1 and 2 (today's Section 1)

Section 1 holds the passages and the strengths evaluation. Section 2 holds the comparison and the reflection, and waits on Section 1.

| Where | Now | New |
|---|---|---|
| Passages heading | Read these passages before continuing | **Scripture on gifts** |
| Passages confirm button | I've read these passages and I'm ready to continue | Remove |
| Activity text | This section uses the Strengths Assessment – a tool where you sort and rate your strengths across 36 areas. You can also invite people you trust to do the same for you. | **This section uses the strengths evaluation, where you sort and rate your strengths across 36 areas. You can also invite people you trust to do the same for you.** |
| Activity button | Open Strengths Assessment → | **Open the strengths evaluation →** |
| Activity, once done | You've completed the assessment. You can review your results any time. | **You've completed the strengths evaluation. You can review your results any time.** |
| Activity status pill | Not started | Remove |
| Reflection prompt (now in Section 2) | Having completed the assessment and read the passages above, summarise… | **Having completed the strengths evaluation, read the passages on gifts and seen how others see you, summarise…** (rest unchanged) |
| Reflection placeholder | …your assessment results… | …your **strengths evaluation** results… |
| Gate message (both) | Complete the Strengths Assessment to continue. | **Complete the strengths evaluation to continue.** |
| "Complete the…" prompts after the finish button | (each prompt) | Show only after "I've finished Section 1" is pressed and refused |

## Results and comparison

| Where | Now | New |
|---|---|---|
| Results page button, fewer than {min} answered | Compare with how others see you → | **Invite people who know you →**, leading to Five trusted voices, with ticket 81's "how many more" phrase beside it |
| Results page button, {min} or more answered | Compare with how others see you → | unchanged |
| Comparison description | Comparing your self-assessment with… | Comparing your **strengths evaluation** with… (and the coach's version: "{name}'s strengths evaluation") |

## Five trusted voices and links

| Where | Now | New |
|---|---|---|
| "Add at least 3 people." | shown under the list | Show only after a press that it refuses |
| Link dialog (observer and coach) | This link is shown only this once. If you lose it, reissue it. | **This link is shown only this once. If you lose it, make a new one here; the old one will stop working.** |
| Link button | Reissue link | **Make a new link** |
| Coach share, expired link | …Reissue it from your coach page… | …**Make a new one** from your coach page… |

## Walk with a coach

| Where | Now | New |
|---|---|---|
| Second thought | None of this rules {name} out, and it may be worth simply raising it with them. "Would you be able to mostly ask questions rather than give me advice?" is a fair thing to ask upfront. | **None of this rules {name} out. When {name} opens their link, they'll be asked to agree to the same {count} things you've just answered, including asking questions rather than handing out answers.** |
| "Choose a coach and send them their link." | shown under the screen | Show only after a press that it refuses |
| Coach's details | Their email (optional) | Remove the field. Only the coach's name is kept |
| Coach's link page, privacy line | We keep only your answer, accept or decline, with the name and email address {name} provided. | We keep only your answer, accept or decline, with the name {name} provided. (rest unchanged) |
| You've chosen {name} | (no way on) | Add a **"Back to the hub"** button |
| Coach brief, purpose | …believe what the assessment is telling them… | …believe what the **strengths evaluation** is telling them… |
| Coach brief, avoid | Do not treat the assessment as a verdict. | Do not treat the **strengths evaluation** as a verdict. |
| Coach's link page | {name} finishes the strengths assessment… | {name} finishes the **strengths evaluation**… |

## Observers

| Where | Now | New |
|---|---|---|
| Before sending | You can send your assessment now, or fine-tune… | You can send your **evaluation** now, or fine-tune… |
| Send button | Send my assessment → | **Send my evaluation →** |
| After sending | Your assessment has been sent. | Your **evaluation** has been sent. |
| Second send | Your assessment has already been sent. | Your **evaluation** has already been sent. |

## Section 3: The shape of your life (today's Section 2)

- Body, first paragraph. Now: "Section two, to work through on paper…" New: "Section **three**, to work through on paper…"
- Body, second paragraph. Now: "Sections two to four make up the middle of the course…" New: "Sections **three to five** make up the middle of the course…"
- Body, last paragraph. Now: "…it can take a while to get others to provide their assessments of you – don't let that stop you making progress on the workbook." New: "…it can take a while to get others to provide their **evaluations** of you – don't let that stop you making progress on **your journey**."
- The words otherwise stay. Its layout is a separate fix.
- The PDFs themselves say "Section 2", "Section 3" and "Section 4" until the content owner's revised versions arrive with the new numbers.

## Demo only

- "Retake the assessment" becomes **"Retake the strengths evaluation"**, wherever it appears.

## Not in this sheet

- The privacy page: it waits on the controller and retention answers.
- Facts the content owner hasn't confirmed: the 71%, 86% and 100% figures, and "95% of their week".
