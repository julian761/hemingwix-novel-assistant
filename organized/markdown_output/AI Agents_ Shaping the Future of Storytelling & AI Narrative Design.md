---
title: "Ai Agents  Shaping The Future Of Storytelling & Ai Narrative Design"
content_type: "ai-analysis"
created_date: "2025-08-30"
source: "transcoded"
status: "cleaned"
---

**AI Agents: Shaping the Future of Storytelling & AI Narrative Design** \-   
YouTube \- https://www.youtube.com/watch?v=NhMTWDjsLVI

**Transcript:**  
(00:00) Can a swarm of AI agents write the next great novel? Well, narrative design is a great example of applying multi-agent pipelines to a problem space, because it empowers something that large language models struggle to do by themselves. So even if you're not planning on using an AI author to create a literary masterpiece, stick around to see how multi-agent pipelines can be applied to all sorts of complex problems like this.

(00:31) Now, an LLM that can crank out a blog post or even a short story. But for rich storytelling narratives, it's not long until the cracks start to emerge. Now, I've made my shameful confession on this channel before that I use LLMs to create fan fiction short stories, but they're not always the best because there are a number of LLM shortfalls that do pop up.  
(01:01) So what sort of shortfalls? Well, one of them comes down to the context window. Context window overflow. As the token limit hits, the model can forget earlier bits of a story. Now today's LLMs, they have really large context windows that should be big enough to store really even the longest narrative. But their recall of specific facts from that context window is far from perfect.

(01:28) They do sometimes forget. The second factor comes down to style drift. Now, what starts as a tense legal thriller may kind of drift into a bit of a generic tale as the model regresses to outputting in its default voice, and also, there is no self-critique loop. The model is continually outputting new tokens without reflecting on how the narrative is holding up, and the root cause of all of this is that all logic and memory and judgment, they all live in one forward pass.

(02:08) There's no long-term scratchpad. There's no specialized roles, there's no critical editor. But that's where a multi-agent pipeline comes in. Now a vanilla LLM, what does that do? Well it predicts. It predicts the next token in a sequence. That's how LLMs work. But an agentic stack goes through a bit more than that.

(02:32) So the first stage is it perceives its environment. And once it's done that, it starts to think about strategy. When it's thought about it, it then acts on that strategy. And then what makes the authentic stack so interesting is that there is then this self-reflection area here where the model actually goes back and reflects and goes round again and again.

(03:01) Now these agents, they include a number of other things as well. So they will have built into them a memory tier. Now that memory tier might be some short-term memory like a scratchpad. Or it might be long-term memory like a vector database store. And there's also going to be access to tools. Agents do make use of tools.

(03:27) So, a narrative is being constructed. And the agent then could say make a rest call to a lore database to understand a little bit more about the world that it's building. Now where this gets interesting is that when we introduce that multi-agent pipeline that I keep mentioning, well, we get to use multiple agents, and each one of those agents owns a narrow competency.

(03:53) Now a multi-agent pipeline for a narrative design pipeline. It might consist of five different agents. So the first one of those, that might be the narrative planner agent. That turns a prompt for, say, write me a space opera noir into a beat sheet with scene structure and thematic goals. The second agent that might be a character forge agent that would generate bios and backstories and motivation graphs and store them in a vector database for recall so they don't get lost in the context window.

(04:30) The third agent that might be a scene writer agent that turns each beat into prose, using the character forge agent to ensure continuity. The fourth agent might be a voice style agent that applies a consistent target writing style to the context. And then number five, the critic. The critic agent that that really scores the the tone, the pacing, the plot coherence of all this generated content.

(05:00) And it generates change requests. And it's the critic agent that forms the self-reflection loop here that is missing from those pure LLM runs. Now, this overcomes those shortfalls I mentioned earlier. So context window overflow is no longer a problem because character and law facts live in external memory.

(05:22) Agents only retrieve the current scene that they need. Style drift is avoided as the voice style agent enforces a reference corpus and no self-critique. Well, that's the thing of the past, because the critic agent iteratively checks goals and coherence.
