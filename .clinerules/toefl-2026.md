# Project: TOEFL 2026 GenSheet Development
# ID: proj_663fa10239e64b2aa5063160a74b1fbb


# Project: TOEFL 2026 GenSheet Development
# ID: proj_663fa10239e64b2aa5063160a74b1fbb


# TOEFL 2026 Gensheet Logic Improvement Plan

This document outlines the tasks and progress for improving the gensheet logic based on feedback from the Google Doc.

## Task List

### Key Takeaways

- [ ] **Stop using "for example."** Just give an example. Don’t signal it.
- [ ] **Stop using big lists** both in the intact sentences and the sentences with missing letters.
- [ ] **Split the missing letters across two sentences.** The first sentence will have most of the missing letters. The second sentence can have missing letters only at the beginning.
- [ ] **Have two complete sentences at the end,** after the missing letters.
- [ ] **Don’t always need an obvious “xxx is yyy” opening.**
- [ ] **Vocab shouldn’t be so technical.**

### Specific Feedback

- [ ] **[a] CUT - not TOEFL, sensitive**
- [ ] **[b] The ETS content often ends with an example, but doesn't specifically use "for example" so you should cut that out of your questions, and prompt the AI to avoid overdoing it.**
- [ ] **[c] Avoid including long lists. I spotted one sentence that might be described as a list in the ETS content. Long lists is a hallmark of AI answers. ChatGPT loves to produce lists when asked to write about academic content.**
- [ ] **[d] Maybe the aforementioned "long list" is what you mean by "long-winded." Don't overuse them.**
- [ ] **[e] Same as above, long-winded "for example" sentences, is that all right? @mgoodine@gmail.com**
- [ ] **[f] Not sure what your question for me is... but note my earlier comment about "for example." You should give an example... but should avoid those specific words.**
- [ ] **[g] Words like "bulges" and "inertial" and "centrifugal" are far too difficult. Add something in the prompt is to write in layman's terms, so a newcomer would understand, while keeping the freshman-level university textbook level**
- [ ] **[h] Indeed. Those words are very hard, especially when they become the incomplete words! The trickiest and most technical word I think I saw in the ETS samples was "cognitive." And that was in the crappy PDF.**
- [ ] **[i] We might have to write something in the prompt so the second and third sentences do not use proper nouns.**
- [ ] **[j] I can see in your samples that you are trying to shove ALL of the missing letters into one giant (second) sentence. But in the ETS materials they often get split between TWO sentences (the second and third). In this case sometimes both sentences are missing letters all the way through. In other cases the second sentence is totally "unintact," while the third sentence is missing letters only at the beginning. Check out the one on CLIMATE (loom) to see what I mean.**
- [ ] **[k] CUT - too difficult and abstract**
- [ ] **[l] I'll skip over the ones you have marked thusly.**
- [ ] **[m] This is way too technical.**
- [ ] **[n] These long-winded final sentences keep coming up.**
- [ ] **[o] Yeah, obviously you noticed the same thing I did. The problem is the use of a list. Adjust the prompt to specifically avoid them.**
- [ ] **[p] "Hormone" is probably too hard and technical. Probably.**
- [ ] **[q] Now you've got a list all the way through the sentence with missing letters. That's going to make it really really really hard for the student since they don't have much to go on. Try splitting this into two sentences. Something like: "Chronic stress alters our mood and can even weaken our immune system. Because it can also impair our concentration, it can be challenging to develop proper coping behaviors." That's off the top of my head and might not have the best words in the best positions. But you get what I mean. Sharing the incomplete words over two sentences will make the passage flow better and eliminate the big ugly list.**
- [ ] **[r] This has the same problem as above - "for example" and then a giant list. This is the biggest list so far. Look at the PALEONTOLOGY and FOSSILS samples from the ETS content (Loom videos). They have two intact sentences at the end! Splitting this up into two concise sentences would solve the problem.**
- [ ] **[s] We need more variety in sentence structure. The opening sentence of each of the examples from ETS is formulaic, but there is more variety in the rest of the passages.**
- [ ] **[t] I feel like "museum" and "photography" are a bit too basic. Maybe. I know one of the ETS question is about "rain" but they do tend to be a little more technical.**
- [ ] **[u] This example is better.**
- [ ] **[v] Can you grasp what I mean now? This is another list. They all have lists. Compare it to, for example: " Paleontologists also use fossils to learn about ancient environmental conditions. Finding marine fossils in landlocked areas, for example, suggests that these regions were very likely underwater once upon a time." Or even: "Logical reasoning is not just important for lawyers and scientists. It is also essential in everyday situations, from choosing the best investment options to resolving interpersonal conflicts." No lists there.**
- [ ] **[w] I revised this one quickly to show you the approach I mean.**
- [ ] **[x] List, list, list. I will stop mentioning this now, as I think you get my point.**
- [ ] **[y] I'll mention it again. This is a long list. The next sentence is a list as well.**
- [ ] **[z] See above. Resist the urge to specifically use "for example."**
- [ ] **[aa] I chopped up this final sentence into two just to, again, show you what I am getting at here.**
- [ ] **[ab] Here you have lists on either since of the conjunction! I would say: "Community radio stations serve a vital function by broadcasting local news and weather reports to local audiences. This can increase both civic engagement and public safety, especially in remote regions with limited communication infrastructure." Or something like that.**
- [ ] **[ac] Way too hard.**
- [ ] **[ad] Way way way way too hard to have a missing segment.**
- [ ] **[ae] See above. Setting aside the fact that the vocabulary is way too hard, you could split the missing letters over two sentences. Like: "Cells accumulate damage over time, and our body's systems are unable to keep up with damage to critical organs. In time, this leads to muscle loss and weakened bones......" Or something like that,**
- [ ] **[af] See what I mean? Not EVERYTHING needs to be a definition. Look at the ETS question about water, for example.**
- [ ] **[ag] "spinal cord" is a bit too much. You can just say "spine and brain" obviously.**
- [ ] **[ah] I don't even know what this means. Very technical.**
- [ ] **[ai] See above**
- [ ] **[aj] So I have split this into two sentences. Most of the blanks could go in the first sentence, with just a few at the beginning of the second sentence. Once you realize that the second sentence can have just a few blanks and then be mostly complete you will have a lot more freedom in designing the content!**
- [ ] **[ak] Duplicate?**

# Internal Project Rules & Guidelines

This section outlines the internal rules and best practices for the TOEFL 2026 GenSheet Development project.

## Google Sheets References

-   **Main Generation Sheet:** [TOEFL Reading - Complete the Words - Generation](https://docs.google.com/spreadsheets/d/1mFFyQ9EsjIZQyq3fWJCSLc78aGaIAdXrFGclXvwcLHI/edit)
    -   **`TOEFL2026_Passages` (GID: 562354263):** Main output sheet for generated passages.
    -   **`Config` (GID: 188417004):** All generation parameters are controlled from this sheet.
    -   **`Topics` (GID: 350240275):** List of topics for passage generation.

## Feedback and Configuration Updates

When new feedback is received, the following process must be followed to ensure the system remains synchronized:

1.  **Update Creation Instructions:** The relevant `Creation-Instructions.md` file for the question type should be updated to reflect the new feedback.
2.  **Update `Config` Sheet:** The `Config` sheet in the main generation Google Sheet must be updated to match the new requirements. This includes, but is not limited to, `PASSAGE_LENGTH_MIN`, `PASSAGE_LENGTH_MAX`, and the `PROMPT_REQUIREMENTS`.
3.  **Verify Script Logic:** The `PassageGenerator.gs` script should be checked to ensure it correctly implements the logic dictated by the `Config` sheet. The script should be fully driven by the `Config` sheet to avoid inconsistencies.
