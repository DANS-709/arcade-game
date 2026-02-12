from openai import OpenAI

client = OpenAI(api_key=None) # гитхаб не позволяет закомитить вместе с моим api-ключом

def ask_npc(system_prompt, user_message):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=200
    )
    return resp.choices[0].message.content