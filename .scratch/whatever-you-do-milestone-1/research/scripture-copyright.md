# Scripture copyright notices and quoting limits

> ✨ Researched and drafted with AI assistance.

Research for ticket 39 (`issues/39-scripture-copyright-notices.md`). Pages were fetched on 7 October 2026. Where a primary page could not be reached, this note says so, and the claim is marked **unverified**.

## Bottom line for ticket 39

The app shows two translations, so it needs two notices, each in its "marked" form. The pathway passages are the ESV Anglicised (their wording matches it except for small edits), so they need the Anglicised ESV digital notice. The homepage verse (Colossians 3:23) is NIV, and because the operators are in the UK, the NIV notice comes from Hodder & Stoughton. Both notices belong on one copyright or credits page that every page links to, for example from the footer. Each passage then shows "(ESV)" or "(NIV)" beside its reference: Crossway's API terms ask for "ESV" with every quotation, and both publishers' marked notices only work if each quotation carries its letters. Our quoting is well within every limit. The faithful port quotes 30 ESV verses, the workbook adds 1 ESV and 3 NIV verses, the homepage adds 1 NIV verse, all far below the 500-verse allowance each publisher gives. No one book comes near half quoted. The condition to watch is that scripture must stay under 25% of "the work": on a rough word count it is about 21% of the faithful-port document, and 8% of `whatever-you-do.json`. Two things need fixing or a decision. First, the stored text has small edits: "baptising" where the ESV Anglicised has "baptizing", "forever" where it has "for ever", and two cuts in Acts 18:2 and Psalm 37:7 with no ellipsis. Crossway's API terms forbid changing words and require an ellipsis for any cut. Second, the ESV notice forbids quoting the ESV in any publication released under a Creative Commons licence, so the pathway documents must never go out under one.

## 1. ESV, ESV Anglicised, NIV and NIV Anglicised

### ESV (Crossway)

**Rights holder.** Crossway, a publishing ministry of Good News Publishers, holds the ESV and grants permission for it ([crossway.org/permissions](https://www.crossway.org/permissions/)).

**Limits without permission.** These are the same for print, digital and audio ([crossway.org/permissions](https://www.crossway.org/permissions/)):

> The ESV text may be quoted in print, digital, and audio formats up to and inclusive of five hundred (500) verses without a formal license or express written permission of Crossway, provided that the verses quoted do not amount to more than one-half of any one book of the Bible or its equivalent measured in bytes, nor do the verses quoted account for twenty-five percent (25%) or more of the total text of the work in which they are quoted, and the verses are not being quoted in a commentary or other biblical reference work.

The digital section lists "Website", "Blog", "Social Media" and "Writing a book (Ebook)" as common uses ([crossway.org/permissions](https://www.crossway.org/permissions/)).

**Required notice.** The digital section says: "Notice of copyright must appear as follows on digital works quoting from the ESV" ([crossway.org/permissions](https://www.crossway.org/permissions/)):

> Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard Version®), © 2001 by Crossway, a publishing ministry of Good News Publishers. ESV Text Edition: 2025. The ESV text may not be quoted in any publication made available to the public by a Creative Commons license. The ESV may not be translated in whole or in part into any other language. Used by permission. All rights reserved.

**Where it goes.** For print it goes "on the title page or copyright page of printed works quoting from the ESV, or in a corresponding location when the ESV is quoted in other media" ([crossway.org/permissions](https://www.crossway.org/permissions/)). In a web app, the corresponding location is a copyright or credits page.

**More than one translation.** Crossway says ([crossway.org/permissions](https://www.crossway.org/permissions/)):

> When more than one translation is quoted in printed works or other media, the foregoing notice of copyright should begin as follows: "Unless otherwise indicated, all Scripture quotations are from… [etc.]"; or, "Scripture quotations marked (ESV) are from… [etc.]."

**When "(ESV)" alone is enough.** Initials alone are enough only for non-saleable media ([crossway.org/permissions](https://www.crossway.org/permissions/)):

> When quotations from the ESV text are used in non-saleable media, such as church bulletins, orders of service, posters, transparencies, or similar media, a complete copyright notice is not required, but the initials (ESV) must appear at the end of the quotation.

A public web app is not on that list, so we should give the full notice and also put "(ESV)" beside each passage.

**Trademark.** "The "ESV" and "English Standard Version" are registered trademarks of Crossway. Use of either trademark requires the permission of Crossway." ([crossway.org/permissions](https://www.crossway.org/permissions/)). Naming the translation beside a quotation is the use Crossway itself asks for. Using the marks for anything else, such as a logo, is not covered.

**Websites and apps.** Crossway's ESV API terms are stricter than its general guidelines, and they apply only if we fetch the text through the API (see section 4). They also say how to treat the text itself, which is a useful guide for us in any case ([api.esv.org](https://api.esv.org/)):

> You may not change any of the words in the text. You may choose to omit certain features, such as headings, footnotes, cross-references, and verse numbers. You may also omit portions of verses or sections quoted if you include an ellipsis (…) indicating that you are omitting them, and only if such omissions do not change the meaning of the verses or sections being quoted.

### ESV Anglicised (Crossway and HarperCollins)

**Rights holder.** Crossway's own copyright page for the ESV Global Study Bible names HarperCollins as the contact for the Anglicised text ([esv.org copyright page](https://www.esv.org/resources/esv-global-study-bible/copyright-page/)):

> Permission requests for use of the anglicized ESV Bible text that exceed the above guidelines must be directed to: HarperCollins Religious, The News Building, 1 London Bridge Street, London SE1 9GF, UK.

Bible Gateway, which HarperCollins Christian Publishing operates, lists the ESVUK with "Publisher: HarperCollins". It says "Permission requests for use within the UK and EU that exceed the above guidelines must be directed to HarperCollins Religious", but gives an older Fulham Palace Road address ([Bible Gateway, ESVUK](https://www.biblegateway.com/versions/English-Standard-Version-Anglicised-ESV-Bible/)).

**Primary page not found.** I could not find a permissions page for the Anglicised ESV on a HarperCollins UK or Collins website. The guidelines and notice text below come from the Bible Society of South Africa, which hosts the "English Standard Version Anglicised 2016" under licence and reproduces the publisher's guidelines ([biblesa.co.za/esv](https://biblesa.co.za/esv)). The Bible Society is a licensee, not the publisher, so treat these texts as **unverified against HarperCollins's own page**.

**A HarperCollins copyright page, checked 7 October 2026.** The developer read the copyright page of *Holy Bible: English Standard Version (ESV) Anglicised Black Gift and Award edition* (Collins Anglicised ESV Bibles, ISBN 9780007466023) through Amazon UK's preview ([Amazon UK listing](https://www.amazon.co.uk/dp/0007466021)). It is a primary source, but from 2012: "This edition first published in Great Britain in 2012 by HarperCollinsPublishers", and "Anglicized edition © 2002 HarperCollinsPublishers". It gives no ESV Text Edition year. Its terms are the older, looser ones: 1,000 verses, no complete book, and under 50% of the work. Its print notice reads:

> Scripture quotations are from The ESV® Bible (The Holy Bible, English Standard Version®), published by HarperCollinsPublishers, © 2001 by Crossway. Used by permission. All rights reserved.

It confirms three things: HarperCollins publishes the Anglicised edition; it spells it "Anglicized"; and, where more than one translation is quoted, the notice begins "Unless otherwise indicated, all Scripture quotations are from … [etc.]". Permission requests "within the UK and EU" go to HarperCollins, and all others to Crossway. It does not settle the current digital wording, which differs from the 2016 digital notice below. A 2014 Bible Society UK edition, "English Standard Version with British text", likewise prints Crossway's plain notice, with ESV Text Edition 2011 and a 1,000-verse limit ([Bible Society UK, PDF](https://www.biblesociety.org.uk/uploads/content/shop/files/ESV-New-British-Texts.pdf)). The terms have changed over time, so the stricter current ones are the safe reading. Bible Gateway, checked the same day, credits an ESVUK passage only with "The Holy Bible, English Standard Version Copyright © 2001 by Crossway Bibles, a division of Good News Publishers." ([Bible Gateway, ESVUK Matthew 28:18–20](https://www.biblegateway.com/passage/?search=Matthew%2028%3A18-20&version=ESVUK)). That is its own credit line for licensed display, not the notice it asks others to use. Its ESVUK "Copyright" tab ([Bible Gateway, ESVUK](https://www.biblegateway.com/versions/English-Standard-Version-Anglicised-ESV-Bible/)) gives the trademark, non-saleable-media and reference-work rules and the permissions contacts ("Permission requests for use within the UK and EU that exceed the above guidelines must be directed to HarperCollins Religious", at the older Fulham Palace Road address), but no notice text and no verse limits. So no HarperCollins source found online gives the current digital notice. Settling it needs HarperCollins Religious in writing.

**Limits.** These match the US ESV: 500 verses, no more than half of any one book, and under 25% of the total text of the work. A lower 50-verse limit applies to artwork and stationery, and to music ([biblesa.co.za/esv](https://biblesa.co.za/esv)).

**Notice for digital works** ([biblesa.co.za/esv](https://biblesa.co.za/esv)):

> Scripture quotations are from the Anglicized ESV® Bible, copyright © 2002 by Crossway and HarperCollins Publishers, London. Used by permission. All rights reserved. May not copy or download more than 500 consecutive verses of the Anglicized ESV® Bible or more than one half of any book of the Anglicized ESV® Bible.

**Notice for printed works**, which suits the workbook PDF ([biblesa.co.za/esv](https://biblesa.co.za/esv)):

> Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard Version®), copyright © 2001 by Crossway, a publishing ministry of Good News Publishers. ESV Text Edition: 2016. Anglicized English Standard Version copyright © 2002 by Crossway and HarperCollins Publishers, London. Used by permission. All rights reserved.

**Who handles requests.** "For such requests that initiate in the UK or EU, contact HarperCollins Publishers, London. For all other such requests, contact […], or Crossway, Attn: Permissions, 1300 Crescent Street, Wheaton, IL 60187." ([biblesa.co.za/esv](https://biblesa.co.za/esv)). The page hides the email address.

**Creative Commons.** The Anglicised notice above does not repeat the US notice's Creative Commons sentence. The underlying text is still Crossway's, so the safe reading is to keep the ban (see the bottom line).

### NIV and NIV Anglicised (Biblica, Hodder & Stoughton, Zondervan)

**Who grants permission, and where.**

- Biblica owns the NIV. Hodder & Stoughton is its publisher for the UK, the EU and EFTA. Zondervan (HarperCollins Christian Publishing) is its publisher for the USA and Canada. Biblica itself handles the rest of the world, which includes South Africa ([Hodder permissions guidance](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/); [Biblica permissions](https://www.biblica.com/permissions/)).
- Hodder: "Hodder & Stoughton are the publishers of the NIV in the UK, EU and EFTA" ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)).
- Biblica's live page returned HTTP 403 to every fetch. I read it as the Internet Archive's copy of Biblica's own page, captured on 16 September 2026 ([web.archive.org snapshot of biblica.com/permissions](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/)). That copy routes "United Kingdom, EU & EFTA" to Hodder & Stoughton, and routes "Rest of the World (outside North America, the UK, and Europe)" to Biblica, Inc.
- Hodder's page is on johnmurraypress.co.uk, which belongs to Hodder's parent group. It is headed "Permissions Guidance" and speaks as "the UK publisher for the New International Version" ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)).

**Hodder's terms (UK, EU and EFTA).** Hodder covers websites under "published media" ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)):

> 2. Using the NIV in published media (e.g. books, eBooks, magazines, websites, cards, artwork)
>
> Up to five hundred (500) verses may be quoted for commercial or non-commercial use in any form (written, visual, or electronic), without express written permission from Hodder.
>
> Please use the following notice of copyright on the title or copyright page of the work:
>
> Scripture quotations [marked NIV] taken from the Holy Bible, New International Version Anglicised Copyright © 1979, 1984, 2011 Biblica. Used by permission of Hodder & Stoughton Ltd, an Hachette UK company. All rights reserved. 'NIV' is a registered trademark of Biblica UK trademark number 1448790.
>
> Please note: if the verses quoted amount to a complete book of the Bible or account for 25 per cent or more of the total text of the work in which they are quoted (based on word count), please contact us for permission as there may be a fee for this type of use.

The free allowance covers commercial use as well as non-commercial. "(NIV)" alone is enough only "For use in churches, including bulletins, orders of service, posters, transparencies or similar media, including video, PowerPoint and other onscreen use" ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)). A public website falls under section 2, so it needs the full notice.

**Biblica's terms (rest of the world, including South Africa)**, from the archived copy of [biblica.com/permissions](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/):

> You may quote Biblica Bible text in any form (written, visual, electronic, or audio) without requiring written permission, provided that all of the following conditions are met:
> - 500 verses or fewer are used in total, and
> - The verses quoted do not constitute a complete book of the Bible, and
> - The verses quoted make up less than 25% of the total text in your product or publication, and
> - Each use includes proper copyright acknowledgment.
>   - (If needed, Biblica can provide the correct copyright acknowledgment.)

> Please note that, when posting to a media platform, the General Use Guidelines will apply to that platform as a whole, not to individual posts, episodes, articles, or other content.

The archived page gives no notice text of its own. It also answers "Can I use Biblica text in an app or website?" with "Yes. This use requires written permission, which could be in the form of an Express License if your use qualifies, or under a Standard Publishing License". On its face this conflicts with the general allowance above. The FAQ probably means hosting Bible text in an app, not quoting a few verses, but that reading is **unverified**. The same page says AI or machine-learning use of Biblica content needs a licence. It defines fundraising, donor gifts and premiums as commercial use.

**Zondervan's terms (USA and Canada).** For reference: the same 500 verses, but with "not more than 50% of a complete book", plus the 25% rule ([HarperCollins Christian permissions](https://www.harpercollinschristian.com/sales-and-rights/permissions/)). The US notice:

> Scripture quotations taken from The Holy Bible, New International Version®, NIV®. Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc. Used with permission of Zondervan. All rights reserved worldwide. www.zondervan.com

**Where the NIV notice goes on a website that quotes one verse.** Hodder asks for the notice "on the title or copyright page of the work". The work is the website as a whole, and Biblica says the guidelines apply "to that platform as a whole". The notice therefore goes on the site's copyright or credits page, not under the verse itself. Because the site quotes two translations, we use the "[marked NIV]" form, and the homepage verse shows "(NIV)" beside "Colossians 3:23" so that the marked notice points at it. Biblica's merchandise answer points the same way, though it is about merchandise: "the acronym NIV must appear immediately after the quoted Bible verse or passage" ([Biblica, archived](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/)).

### Which terms apply to an audience in the UK, the EU and South Africa

- **What the publishers say.** They divide permission by territory of publication. Hodder covers the NIV in the UK, EU and EFTA; Biblica covers the rest of the world, including South Africa ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/); [Biblica, archived](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/)). HarperCollins covers the Anglicised ESV for requests that "initiate in the UK or EU" ([biblesa.co.za/esv](https://biblesa.co.za/esv)).
- **Our reading.** The operators are in the UK, so the UK terms apply: Hodder's NIV Anglicised notice, and HarperCollins and Crossway for the Anglicised ESV. Neither publisher says how to treat one website that is also read from South Africa, so this is **unverified**.
- **Why it matters less than it seems.** The free limits are the same in every territory (500 verses, under 25%, no whole book or no more than half a book). Only the notice wording and the contact for larger requests differ.
- **Which NIV text we quote.** Colossians 3:23 and 2 Timothy 3:16–17 read the same in the NIV (UK) as in the workbook ([Bible Gateway, NIVUK Colossians 3:23](https://www.biblegateway.com/passage/?search=Colossians%203:23&version=NIVUK); [Bible Gateway, NIVUK 2 Timothy 3:16–17](https://www.biblegateway.com/passage/?search=2%20Timothy%203:16-17&version=NIVUK)). Hodder's "New International Version Anglicised" notice is therefore accurate for those verses.

### Confirming the edition of the pathway passages

I compared each passage in `pathways/whatever-you-do-faithful-port.json` word for word with the ESVUK and the ESV on Bible Gateway, which HarperCollins operates. The three passages shared with `whatever-you-do.json` are identical in both documents. Bible Gateway is the publisher group's own site, but it is not a Crossway text, so treat the match as strong but not formal proof. The results:

- **Matches the ESVUK, not the US ESV.** "neighbour" (Matthew 22:39) and "labour" (1 Corinthians 15:58) match the ESVUK. The US ESV has "neighbor" and "labor" ([Bible Gateway, ESVUK](https://www.biblegateway.com/passage/?search=Matthew%2022%3A39&version=ESVUK)).
- **Matches neither.** "baptising" (Matthew 28:19) is in neither edition: both have "baptizing" ([Bible Gateway, ESVUK Matthew 28](https://www.biblegateway.com/passage/?search=Matthew%2028%3A18-20&version=ESVUK)). The ESVUK keeps "-ize" spellings.
- **Matches the US ESV.** "forever" (1 Peter 4:11) matches the US ESV. The ESVUK has "for ever".
- **Cut in Acts 18:2.** The passage leaves out "because Claudius had commanded all the Jews to leave Rome", ends the sentence at "Priscilla.", and starts verse 3 "And because". The ESVUK has "…Priscilla, because Claudius had commanded all the Jews to leave Rome. And he went to see them, and because…" ([Bible Gateway, ESVUK Acts 18:1–4](https://www.biblegateway.com/passage/?search=Acts%2018%3A1-4&version=ESVUK)).
- **Cut in Psalm 37:7.** The passage stops at "wait patiently for him." and leaves out "fret not yourself over the one who prospers in his way, over the man who carries out evil devices!"
- **Everything else matches.** All other words match the ESVUK exactly.

So the text is the ESV Anglicised with light editing. The cuts carry no ellipsis, and "Acts 18:1–4" and "Psalm 37:3–7" read as complete verse ranges. Crossway's API terms allow cuts only "if you include an ellipsis (…)" and never allow changed words ([api.esv.org](https://api.esv.org/)). Its general guidelines do not say this, but the safe course is to restore the exact ESVUK text, or to mark the cuts with "…".

## 2. Our quoting against the limits

### Verse counts

| Where | Translation | Passages | Verses |
|---|---|---|---|
| `whatever-you-do-faithful-port.json` | ESV Anglicised | Romans 12:6–8 (3), 1 Cor 12:8–10, 28–30 (6), 1 Peter 4:9–11 (3), Matt 28:18–20 (3), Matt 22:36–40 (5), 1 Cor 15:58 (1), Acts 18:1–4 (4), Psalm 37:3–7 (5) | 30 |
| `whatever-you-do.json` | ESV Anglicised | the first three of the above | 12 |
| Homepage footer (`engine/templates/engine/home.html`) | NIV | Colossians 3:23, first half of the verse, no label | 1 |
| Workbook PDF | NIV | Colossians 3:23 on the cover, no label; 2 Timothy 3:16–17, cut with "…", no label | 3 |
| Workbook PDF | ESV | Ephesians 2:10 on the back page, no label (the wording matches the ESVUK) | 1 |

**The workbook's "(NIV)" label.** The label sits on the heading "Matthew 16: 24&25 (NIV)". As far as I could find, that page gives the reference as a reading to look up and does not print the text. So it adds no quoted verses, but the workbook still names a translation it does not quote.

**The workbook carries no notice.** Its text contains no copyright notice for either translation.

### Against each limit

- **Verse count.** The allowance is 500 verses for each of the ESV, the ESV Anglicised and the NIV (Hodder, Biblica and Zondervan). We quote at most 31 ESV verses and 4 NIV verses.
- **Share of one book.** The ESV limit is half a book. The NIV limit is no complete book under Hodder and Biblica, and no more than 50% of a book under Zondervan. The most we quote from one book is 8 verses of Matthew (1,071 verses) and 7 of 1 Corinthians (437). That is nowhere near half. Well under 500 verses, the only real risk is a short book: for example, all 25 verses of Jude or 3 John would be a complete book.
- **Share of the total work (25%).** This is the limit that could bite. Crossway counts "twenty-five percent (25%) or more of the total text of the work" ([crossway.org/permissions](https://www.crossway.org/permissions/)), and Hodder counts by word count ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)). On a rough count of every prose string in each JSON document:
  - `whatever-you-do-faithful-port.json`: 543 scripture words out of about 2,541, or about 21%.
  - `whatever-you-do.json`: 254 scripture words out of about 3,246, or about 8%.

  The faithful port is close to the line. Adding passages, or cutting prose, could take it over. If "the work" is the whole app rather than one document, the share is lower. The publishers do not say how to measure "the work" for an app, so that reading is **unverified**.
- **Mixed translations.** Yes, a mixed work needs a notice for each translation. Crossway gives its "Scripture quotations marked (ESV)…" or "Unless otherwise indicated…" forms for works with more than one translation ([crossway.org/permissions](https://www.crossway.org/permissions/)), and Hodder's notice has an optional "[marked NIV]" ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)). Neither publisher's limits pool across translations: each counts its own verses against its own 500.
- **Commentary or reference work.** Both Crossway and Hodder exclude commentaries and biblical reference works from the free allowance. A calling and discipleship pathway is not a commentary in the ordinary sense, but the content owner should confirm we do not describe it as one.

## 3. Public-domain and open fallbacks

**King James Version (Authorised Version).**

- **Outside the UK.** It is in the public domain. A distributor of the text says it is "firmly in the Public Domain" outside the UK ([ebible.org KJV copyright](https://ebible.org/eng-kjv2006/copyright.htm)). That is a secondary source.
- **In the UK.** The Crown's rights in the text sit outside statutory copyright. The Copyright, Designs and Patents Act 1988 keeps "any right or privilege of the Crown subsisting otherwise than under an enactment" ([CDPA 1988 s.171(1)(b)](https://www.legislation.gov.uk/ukpga/1988/48/section/171)). The Act does not name the Bible, so linking that clause to the KJV is my reading and is **unverified**. The Crown grants these rights by letters patent. Cambridge University Press administers them in England, Wales and Northern Ireland, and the Scottish Bible Board in Scotland.
- **What I could not check.** Cambridge's rights and permissions page returned HTTP 403, and its Bible front-matter PDF would not download, so I could not quote Cambridge's own notice or its quoting limits. That part is **unverified**. Search snippets of that PDF suggest a 500-verse allowance for liturgical use, but I could not confirm it.
- **Practical risk.** The letters patent are generally understood to govern printing and publishing in the UK, so this matters for the printed workbook more than for the website. That reading is also **unverified**.

**World English Bible (WEB).**

- **Status.** "The World English Bible is in the Public Domain. That means that it is not copyrighted." ([ebible.org WEB copyright](https://ebible.org/eng-web/copyright.htm)).
- **Notice.** None is required.
- **Trademark.** "'World English Bible' is a Trademark of eBible.org." If you "CHANGE the actual text of the World English Bible in any way, you not call the result the World English Bible any more" ([ebible.org WEB copyright](https://ebible.org/eng-web/copyright.htm)).
- **British edition.** A British Edition exists that uses "British spelling instead of American spelling" and "LORD" in place of "Yahweh" ([worldenglish.bible](https://worldenglish.bible/)). It is the closest open match to our British house style.

**Berean Standard Bible (BSB).**

- **Status.** "The Berean Bible and Majority Bible texts are officially dedicated to the public domain as of April 30, 2023." "All uses are freely permitted." ([berean.bible/terms](https://berean.bible/terms.htm)).
- **Attribution.** It is appreciated but not required: "The Holy Bible, Berean Standard Bible, BSB is produced in cooperation with Bible Hub, Discovery Bible, OpenBible.com, and the Berean Bible Translation Committee." ([berean.bible/terms](https://berean.bible/terms.htm)).
- **Name.** Berean asks that its name not be used for text that varies from the official text.
- **Spelling.** It uses American spelling.

**Others.** Biblica says some of its texts are available under Creative Commons Attribution-ShareAlike at [open.bible](https://open.bible/) ([Biblica, archived](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/)). I did not check which English texts these are or what they require. The ShareAlike condition would also attach to anything we build from them. **Unverified.**

## 4. Bible APIs, for when users pick their own translation

**API.Bible (American Bible Society).**

- **Copyright with each passage.** Yes. The passage object includes a `copyright` field holding "Licensing information for the content" ([docs.api.bible passages](https://docs.api.bible/guides/passages)). The same text is available from `/bibles/{bibleId}` ([care.api.bible](https://care.api.bible/article/388-how-to-find-copyright-and-public-domain-status-of-bibles)).
- **Attribution.** "Attribution is required for all content accessed via API.Bible, with the exception of content that is explicitly labeled as Public Domain." It must be used "exactly as provided", with no paraphrasing, reformatting or abbreviating. Starter-plan users must also show a visible citation and a link to api.bible ([care.api.bible](https://care.api.bible/article/388-how-to-find-copyright-and-public-domain-status-of-bibles)).
- **Content source on the page.** "Any quotation or use of content must clearly indicate the name / identification of the content source title on the page it is being read." (terms, section 7, [api.bible/terms-and-conditions](https://api.bible/terms-and-conditions)).
- **Caching.** Caching is allowed, but "Cached content must be refreshed at least once every 30 days" ([api.bible/faq](https://api.bible/faq); terms, section 11).
- **Usage tracking (FUMS).** API.Bible asks every developer to report each view through FUMS, its Fair Use Management System, which sends a device ID, a session ID and an optional hashed user ID ([docs.api.bible fair use](https://docs.api.bible/guides/fair-use); terms, section 14). **Privacy flag:** this is a transfer of personal data to a US processor and would need its own ADR under UK and EU GDPR.
- **Plans and rate limits.** Starter is free, for non-commercial use only, with 3 copyrighted Bibles and 5,000 calls a month. Pro costs "$29+ / Month" for 150,000 calls ([api.bible](https://api.bible/)). A passage is capped at 200 verses ([docs.api.bible passages](https://docs.api.bible/guides/passages)).
- **Other terms.** Using content to train AI is prohibited (section 9.2). The governing law is Pennsylvania (section 25).
- **NIV.** NIV is listed, but "Not all Bibles are available for all uses (e.g. NIV commercial use not available)" ([api.bible](https://api.bible/)). Biblica names api.bible as an Express Licensing partner for truly non-commercial apps and websites with no AI features ([Biblica, archived](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/)).
- **ESV.** The api.bible home page does not mention it. The full Bible list needs a login, so whether ESV or ESVUK is available is **unverified**.

**ESV API (Crossway, api.esv.org).** All quotes in this item are from [api.esv.org](https://api.esv.org/), except the parameters, which are from [api.esv.org/docs/passage-text](https://api.esv.org/docs/passage-text/).

- **Copyright with each passage.** Yes. `include-short-copyright` (default true) adds "(ESV)", and `include-copyright` adds a full notice. Both "[fulfil] your copyright display requirements".
- **Notice on the site.** The site still needs a copyright page. "On pages that use the ESV text, you must include any copyright notice that is sent with the text. With each quotation, include the letters "ESV."" "Each page on which you use the text must include a link to www.esv.org." The marked form for the copyright page:

  > Scripture quotations marked "ESV" are from the ESV® Bible (The Holy Bible, English Standard Version®), © 2001 by Crossway, a publishing ministry of Good News Publishers. Used by permission. All rights reserved. The ESV text may not be quoted in any publication made available to the public by a Creative Commons license. The ESV may not be translated into any other language.
  >
  > Users may not copy or download more than 500 verses of the ESV Bible or more than one half of any book of the ESV Bible.

- **Limits.** Up to 500 verses or half a book per query, whichever is less. "5,000 queries per day, with no more than 1,000 requests in an hour and no more than 60 requests per minute". Local storage and caching are capped at 500 verses. No page may show more than 500 verses or half a book.
- **Non-commercial only.** "A non-commercial site does not charge for access to any part of the site", whereas "a commercial website is primarily designed to motivate visitors to buy something, to pay for a service, or to give a donation, or it accepts advertising or sponsorships."
- **Statement of faith.** The service is open only to users "consistent with the historic Christian understanding of doctrine", as Crossway summarises it.
- **Apps.** Mobile apps and other digital media are permitted under the same conditions.
- **Edition.** The ESV API serves the ESV. Whether it can serve the Anglicised text is **unverified**: I found no Anglicised option in the docs. It does not offer NIV.

**YouVersion Platform.**

- **Copyright with each passage.** Not on the passage itself. The SDK's `getPassageDisplay` returns `attribution.text` alongside the HTML, taken from the version's `copyright` field: "always display a Bible Version's copyright attribution in accordance with the license agreement" ([developers.youversion.com, Copyright & Attribution](https://developers.youversion.com/sdks/javascript/guides/copyright-and-attribution.md)).
- **Licences.** Access depends on accepting licence agreements for each version ([developers.youversion.com API usage](https://developers.youversion.com/api-usage.md); [licenses API](https://developers.youversion.com/api/licenses)).
- **Non-commercial.** "Non commercial usage (meaning no advertisements/paywalls/subscriptions) in your app" ([help.youversion.com](https://help.youversion.com/l/en/article/72ghg45c41-how-to-sign-up-for-platform)).
- **Other terms.** The terms of use page renders with JavaScript and I could not read it, so caching, storage and rate limits are **unverified**.
- **NIV.** Biblica names YouVersion as its second Express Licensing partner, so NIV is very likely available there for non-commercial use with no AI features ([Biblica, archived](https://web.archive.org/web/20260916222035/https://www.biblica.com/permissions/)). I did not confirm this in a version list.

**NLT API (Tyndale, api.nlt.to).**

- **Translation.** It offers the NLT only.
- **Limits.** Anonymous use allows 50 verses per request and 500 requests a day. With a key, 500 verses per request and 5,000 requests a day ([api.nlt.to](https://api.nlt.to/)).
- **Non-commercial.** Required, though commercial use can be requested at sign-up.
- **Not checked.** The page I read did not cover caching or the notice text, and I did not open Tyndale's own permissions page. **Unverified.**

**NIV through an API.** Yes, through API.Bible and (very likely) YouVersion, but only for non-commercial use with no AI. API.Bible does not offer NIV for commercial use. Neither the ESV API nor the NLT API carries it. Hodder says app licensing of the NIV is by direct contact ("do get in touch") ([Hodder](https://www.johnmurraypress.co.uk/landing-page/hodder-faith-more/)).

## Open questions for the content owner

1. **Exact text.** Should we restore the exact ESV Anglicised text ("baptizing", "for ever", and the full Acts 18:2 and Psalm 37:7)? Or keep the cuts marked with "…" and change the references to match?
2. **Is the app commercial?** Will the app or its site ever take donations, sponsorship, advertising or payment? Crossway's API and Biblica's terms treat donations as commercial, which would rule out the free API routes.
3. **Licence for the pathway documents.** Are the documents, or the repo, ever likely to be released under a Creative Commons licence? The ESV notice forbids it.
4. **The workbook.** Should it gain its own copyright page with the printed Anglicised ESV notice and Hodder's NIV notice? Should its unlabelled quotes (Colossians 3:23, 2 Timothy 3:16–17, Ephesians 2:10) gain "(NIV)" and "(ESV)"?
5. **Matthew 16:24–25.** Should the workbook keep "(NIV)" on a reading it does not quote?
6. **Text edition.** Which ESV text edition do the stored passages follow? Crossway's current notice says "ESV Text Edition: 2025", and the Anglicised notice we found says 2016. Can we get the current Anglicised notice from HarperCollins in writing?
7. **Faithful-port share.** At about 21% scripture, may the faithful port grow? If more passages are planned, should we measure the 25% against the app as a whole, and is the owner comfortable with that reading?
