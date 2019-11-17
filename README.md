# Esther
Personal voice assistant project that mimics those Natural Language Understanding types of AI.

This assistant runs on searching through lists of keywords arranged in a specific pattern, unlike chatbots like RASA who actually KNOW how to properly make use of machine learning to train and create a functional bot. I ain't smart, so this will work.

This bot works by running the user input from a STT engine through lists of keywords to evantually find the most relevant intent the user probably wants.
Each intent contains many "outlines", which is basically a list of words strung together to give some context.
e.g. A sentence containing these words: "give", "me", "upvotes" probably means the user wants upvotes.

The program runs through all possible matches of outlines and ranks the probability of each intent, and picks the one that is most likely to be the user's intent.
