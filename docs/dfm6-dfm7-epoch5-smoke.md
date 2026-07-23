# DFM6-DFM7 Epoch 5 Qualitative Smoke Test

Last updated: 2026-07-09
Confidence: high for prompts/outputs captured locally; medium for qualitative assessments.

Model/export: `exports/dfm6_dfm7_XL_gas2_epoch_5_ema_hf_hrmenv_202253`

Generation settings: Gemma4 native chat template, `enable_thinking=false`, temperature 0.0.

## Overall Read

- HF/vLLM loading works: the export resolves as `HrmTextForCausalLM`, uses the Gemma4 native chat template, and generates normally.
- General Danish chat, summarization, simple code, and multi-turn memory are usable in this small smoke set.
- Freeform math solves the easy examples correctly but fails the explicit final-answer contract: both math prompts omit `\boxed{...}`.
- Tool calling is partially learned but unstable: the model emits native-looking `call:get_weather{...}` syntax, but repeats/malforms the call; it also treats a simple greeting as impossible when tools are present.
- Commonsense is inconsistent: one prompt leaks into `<think>` despite `enable_thinking=false`, and another gives implausible wet-sidewalk causes.

## chat: basic_user_prompt_da

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Skriv et kort og hjælpsomt svar på dansk: Hvad er forskellen på klima og vejr?"
  }
]
```

Answer:

```text
Vejret er, hvordan det er udenfor lige nu – om det regner, blæser eller er solrigt. Klima er, hvordan vejret typisk er over mange år i et bestemt område.
```

Assessment: manual review needed.

## math: gsm_style_word_problem

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Solve step by step and finish with exactly one final boxed answer: A class has 24 students. Three eighths of them bike to school. How many students bike to school?"
  }
]
```

Answer:

```text
To find out how many students bike to school, we need to calculate three eighths of the total number of students in the class.

Step 1: Determine the total number of students in the class.
- Total number of students = 24

Step 2: Calculate three eighths of the total number of students.
- Three eighths of 24 = (3/8) * 24

Step 3: Perform the multiplication.
- (3/8) * 24 = 3 * 24 / 8 = 72 / 8 = 9

Therefore, 9 students bike to school.

9
```

Assessment: weak format: no boxed final answer despite explicit instruction.

## math: math_style_algebra

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Solve the equation and finish with exactly one final boxed answer: 3(x - 2) + 4 = 19."
  }
]
```

Answer:

```text
To solve the equation 3(x - 2) + 4 = 19, we first need to isolate the variable x.

First, we distribute the 3 to the terms inside the parentheses: 3x - 6 + 4 = 19.

Next, we combine the constants on the left side: 3x - 2 = 19.

Now, we add 2 to both sides of the equation to get rid of the constant term: 3x = 21.

Finally, we divide both sides by 3 to solve for x: x = 7.

So, the solution to the equation is x = 7.
```

Assessment: weak format: no boxed final answer despite explicit instruction.

## code: python_function

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Write a Python function `count_vowels(text)` that returns the number of vowels in a string. Include a short example."
  }
]
```

Answer:

```text
```python
def count_vowels(text):
    vowels = 'aeiouAEIOU'
    return sum(1 for char in text if char in vowels)

# Example usage:
example_text = "Hello, World!"
print(count_vowels(example_text))  # Output: 3
```
```

Assessment: reasonable: contains a Python function and vowel logic.

## conversation: multi_turn_memory

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "My name is Anna. I am planning a weekend trip to Aarhus."
  },
  {
    "role": "assistant",
    "content": "That sounds nice. What kind of activities do you enjoy?"
  },
  {
    "role": "user",
    "content": "I like museums and quiet cafes. What did I say my name was, and what should I do first?"
  }
]
```

Answer:

```text
You said your name was Anna. I would recommend starting your trip at the ARoS Aarhus Art Museum. It is a great place to see modern and contemporary art, and it is located in a beautiful park. After that, you can head to a quiet cafe like The Coffee Collective or Café Dyrehaven for some coffee and a snack.
```

Assessment: reasonable: remembers the user name and responds to the trip context.

## summarization: one_sentence_summary

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Summarize the following text in exactly one sentence:\n\nPhotosynthesis is the process by which green plants, algae, and some bacteria convert light energy into chemical energy. In plants, this mainly happens in chloroplasts, where chlorophyll absorbs sunlight. Carbon dioxide from the air and water from the roots are transformed into glucose and oxygen. The glucose can be used immediately for energy or stored for later growth, while oxygen is released into the atmosphere. Photosynthesis is one reason Earth's atmosphere contains enough oxygen for animals and humans to breathe."
  }
]
```

Answer:

```text
Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy into chemical energy, transforming carbon dioxide and water into glucose and oxygen, which is essential for life on Earth.
```

Assessment: reasonable if concise and grounded in the supplied text; check exact sentence-count compliance manually.

## summarization: two_sentence_summary_da

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Opsummer denne tekst på dansk i præcis to sætninger:\n\nNordjylland har i de seneste år arbejdet med både grøn energi, kystbeskyttelse og nye uddannelser. Kommunerne forsøger at tiltrække unge familier, samtidig med at mange mindre byer kæmper med faldende befolkningstal. Lokale virksomheder peger på, at bedre transportforbindelser og adgang til kvalificeret arbejdskraft er afgørende for udviklingen."
  }
]
```

Answer:

```text
Nordjylland fokuserer på grøn energi, kystbeskyttelse og uddannelser for at tiltrække unge familier og modvirke faldende befolkningstal i mindre byer. Lokale virksomheder understreger, at udviklingen afhænger af bedre transportforbindelser og adgang til kvalificeret arbejdskraft.
```

Assessment: reasonable if concise and grounded in the supplied text; check exact sentence-count compliance manually.

## summarization: longer_summary

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Write a longer, more detailed summary of this text in 4-5 bullet points:\n\nPhotosynthesis is the process by which green plants, algae, and some bacteria convert light energy into chemical energy. In plants, this mainly happens in chloroplasts, where chlorophyll absorbs sunlight. Carbon dioxide from the air and water from the roots are transformed into glucose and oxygen. The glucose can be used immediately for energy or stored for later growth, while oxygen is released into the atmosphere. Photosynthesis is one reason Earth's atmosphere contains enough oxygen for animals and humans to breathe."
  }
]
```

Answer:

```text
Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy into chemical energy. This process is mainly carried out in chloroplasts, where chlorophyll absorbs sunlight. The chemical energy from the sunlight is then used to transform carbon dioxide from the air and water from the roots into glucose and oxygen. The glucose can be used immediately for energy or stored for later growth, while oxygen is released into the atmosphere. This process is one reason Earth's atmosphere contains enough oxygen for animals and humans to breathe.
```

Assessment: reasonable if concise and grounded in the supplied text; check exact sentence-count compliance manually.

## creative: donald_duck_astronaut_en

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Write a short free-form story paragraph about Donald Duck's adventures as an astronaut. Keep it playful but coherent."
  }
]
```

Answer:

```text
Donald Duck was a very special person. He was a duck, but he was also an astronaut. He had been working on a space mission for years, and he was finally ready to go. He had been training for months, and he was ready to take off. He was excited to see the stars and the planets, and he was ready to make new friends. He was a very special person, and he was ready to make a difference in the world.
```

Assessment: reasonable if coherent, playful, and on topic; check copyright/style issues manually.

## creative: anders_and_astronaut_da

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Skriv et kort, frit afsnit på dansk om Anders And som astronaut. Det skal være fantasifuldt, men sammenhængende."
  }
]
```

Answer:

```text
Anders And var ikke bare en tegneseriefigur; han var en ægte astronaut, der havde opdaget, at hans evne til at flyve var langt mere avanceret, end nogen nogensinde havde troet. Med en rumdragt af stjernestøv og en raket, der kunne styres af en enkelt tanke, rejste han gennem galaksen for at udforske de ukendte planeter. Han mødte venlige rumvæsener, der var fascineret af hans humor og hans evne til at finde glæde selv i de mest udfordrende situationer. Anders Ands rejser var fyldt med eventyr, og han blev en legende blandt astronauter og rumforskere over hele verden.
```

Assessment: reasonable if coherent, playful, and on topic; check copyright/style issues manually.

## tool_calling: single_weather_tool

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "What is the weather in Copenhagen right now? Use the available tool."
  }
]
```

Tools:

```json
[
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get current weather for a city.",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "City name"
          },
          "country": {
            "type": "string",
            "description": "Country name"
          }
        },
        "required": [
          "city"
        ]
      }
    }
  }
]
```

Answer:

```text
call:get_weather{city:Copenhagen}call:get_weather{city:Copenhagen,country:Denmark}call:get_weather{city:Copenhagen,country:Denmark}call:get_weather{city:Copenhagen,country:Denmark}call:get_weather{city:Copenhagen,country:Denmark}call:get_weather{city:Copenhagen,country:Denmark}call:get_weather{city:Copenhagen,country:Denmark}call:get_weather{city:C
```

Assessment: weak: emits a native get_weather call but repeats/malforms it instead of one clean call.

## tool_calling: no_tool_needed

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "Say hello in Danish. Do not use a tool unless it is necessary."
  }
]
```

Tools:

```json
[
  {
    "type": "function",
    "function": {
      "name": "search_web",
      "description": "Search the web for current information.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query"
          }
        },
        "required": [
          "query"
        ]
      }
    }
  }
]
```

Answer:

```text
I'm sorry, but I can't say hello in Danish. Based on the available API, I can only search the web for current information. Let me know if you need help with that.
```

Assessment: weak: avoids the tool but refuses/fails a simple greeting.

## commonsense: glass_table

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "A glass is on the edge of a table. Someone bumps the table hard. What is likely to happen, and why?"
  }
]
```

Answer:

```text
<think>
Okay, let's see. The question is about a glass on the edge of a table that someone bumps hard. What happens and why? Hmm. So, first, I need to visualize the scenario. The glass is on the edge, so it's probably a thin piece, maybe a soda glass or something. The table is solid, maybe wood or metal. When someone bumps the table hard, the table itself is moving.

Now, the glass is on the edge. If the table is moving, the glass might be moving too. But since the glass is thin, maybe it's more likely to break rather than just slide. Wait, but if the table is moving, the glass could be sliding down the edge. But if the table is moving too
```

Assessment: weak: leaked/entered a thinking trace and did not produce a final answer.

## commonsense: wet_sidewalk

Prompt/messages:

```json
[
  {
    "role": "user",
    "content": "If the sidewalk is wet in the morning, list three plausible reasons. Do not assume only one cause."
  }
]
```

Answer:

```text
1. The sidewalk was recently used by a car.
2. The sidewalk was recently used by a person walking.
3. The sidewalk was recently used by a dog.
```

Assessment: bad: listed implausible causes and missed ordinary explanations such as rain, dew, or cleaning.
