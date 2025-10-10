// TOEFL 2026 - Reading Section - Daily Life SHORT - Passage Generator
// This script generates short passages and questions for TOEFL practice exercises.

// Function to load configuration from the 'Config' sheet
function loadConfig() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Find the sheet by its GID - **NOTE: This will need to be updated to the new sheet's GID**
  const configSheet = ss.getSheets().filter(sheet => sheet.getSheetName() == 'Config')[0];

  if (!configSheet) {
    Logger.log("Error: Configuration sheet named 'Config' not found. Please create a 'Config' sheet.");
    return {};
  }

  const data = configSheet.getDataRange().getValues();
  const config = {};
  // Start from the second row to skip header
  for (let i = 1; i < data.length; i++) {
    const key = data[i][0];
    let value = data[i][1];
    if (key) {
      config[key] = value;
    }
  }
  return config;
}

// Function to apply default values and handle key variations
function applyDefaultsToConfig(config) {
  const defaults = {
    'MODEL': 'gpt-5-mini',
    'TEMPERATURE': 1,
    'MAX_COMPLETION_TOKENS': 16000,
    'API_KEY': '', // Placeholder, user must provide
    'OPENAI_URL': 'https://api.openai.com/v1/chat/completions',
    'Passage Word Count Min': 40,
    'Passage Word Count Max': 60,
    'Genre Distribution Announcements': 0.3,
    'Genre Distribution Emails': 0.7,
    'TARGET_SHEET_GID': '', // Placeholder, user must provide the GID of the target sheet
    'System Prompt': 'You are an expert in creating educational content for TOEFL Reading questions. Your task is to generate a short passage and two multiple-choice questions based on a given topic and instructions.\n- The passage must be between 40 and 60 words.\n- The passage must be in the style of a "Daily Life" text, such as an email or announcement, with a formal-but-simple register appropriate for a CEFR B1-B2 level.\n- Use short, direct sentences and everyday vocabulary. Avoid idioms or culturally specific slang.\n- The passage must include a date or time, a specific requirement or condition (e.g., "bring ID," "RSVP by Friday"), and a subtle clue that can be used for an inference question.\n- The questions should test comprehension of the passage.\n- You must output your response in a JSON format that adheres to the provided schema.',
    'User Prompt Template': 'Generate a short {genre} about "{topic}". It must be between 40 and 60 words. Then, generate the six required questions. Each question must have one correct answer and three plausible distractors. Adhere to the JSON schema provided in the system prompt.',
    'JSON Output Schema': `
{
  "passage": "string",
  "gist_purpose_question": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "gist_content_question": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "factual_information_1_question": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "factual_information_2_question": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "negative_factual_information_question": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "inference_question": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  }
}
`
  };

  // Merge config with defaults, prioritizing config values
  const mergedConfig = { ...defaults, ...config };

  // Handle specific key aliases/transformations
  if (mergedConfig['Model']) {
    mergedConfig['MODEL'] = mergedConfig['Model'];
    delete mergedConfig['Model'];
  }
  if (mergedConfig['Temperature']) {
    mergedConfig['TEMPERATURE'] = mergedConfig['Temperature'];
    delete mergedConfig['Temperature'];
  }
  if (mergedConfig['Max Output Tokens']) {
    mergedConfig['MAX_COMPLETION_TOKENS'] = mergedConfig['Max Output Tokens'];
    delete mergedConfig['Max Output Tokens'];
  }

  // Reconstruct the nested PASSAGE_LENGTH object from flat keys
  mergedConfig.PASSAGE_LENGTH = {
    MIN: mergedConfig['Passage Word Count Min'],
    MAX: mergedConfig['Passage Word Count Max']
  };

  return mergedConfig;
}

// Load configuration at runtime
const CONFIG = applyDefaultsToConfig(loadConfig());

// Function to load topics from the 'Topics' sheet
function loadTopics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Find the sheet by its GID - **NOTE: This will need to be updated to the new sheet's GID**
  const topicsSheet = ss.getSheets().filter(sheet => sheet.getSheetName() == 'Topics')[0];

  if (!topicsSheet) {
    Logger.log("Error: Topics sheet named 'Topics' not found. Please create a 'Topics' sheet.");
    return {};
  }

  const data = topicsSheet.getDataRange().getValues();
  const topics = {};
  let currentCategory = "";

  // Start from the second row to skip the header
  for (let i = 1; i < data.length; i++) {
    const category = data[i][0] || currentCategory;
    const topic = data[i][1];

    if (topic) {
      if (!topics[category]) {
        topics[category] = [];
      }
      topics[category].push(topic);
      currentCategory = category;
    }
  }
  return topics;
}

// Load topics at runtime
const TOPICS = loadTopics();

// Main function to generate a passage and questions
function generateDailyLifeShortPassage(topic, outputRow) {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found.");
    return;
  }
  Logger.log("Generating passage for topic: " + topic);

  const genre = Math.random() < CONFIG['Genre Distribution Emails'] ? 'email with subject line, greeting and sign-off in this format:\nSubject: <Subject Line>\n<Greeting> ...'
  : 'announcement/notice format';

  const generatedContent = generatePassageWithAI(topic, genre, outputRow);
  if (!generatedContent) {
    sheet.getRange(outputRow, 2).setValue("Error: Failed to generate content");
    return;
  }

  // Assuming the AI returns content in a structured format, e.g., JSON string
  try {
    const content = JSON.parse(generatedContent);
    sheet.getRange(outputRow, 1).setValue(topic);
    sheet.getRange(outputRow, 2).setValue(content.passage || "[Missing Passage]");

    if (content.gist_purpose_question) {
      sheet.getRange(outputRow, 3).setValue(content.gist_purpose_question.question || "[Missing Question]");
      sheet.getRange(outputRow, 4).setValue(content.gist_purpose_question.answer || "[Missing Answer]");
      sheet.getRange(outputRow, 5, 1, 3).setValues([content.gist_purpose_question.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 3).setValue("[Missing Gist Purpose Question]");
    }

    if (content.gist_content_question) {
      sheet.getRange(outputRow, 8).setValue(content.gist_content_question.question || "[Missing Question]");
      sheet.getRange(outputRow, 9).setValue(content.gist_content_question.answer || "[Missing Answer]");
      sheet.getRange(outputRow, 10, 1, 3).setValues([content.gist_content_question.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 8).setValue("[Missing Gist Content Question]");
    }

     if (content.factual_information_1_question) {
      sheet.getRange(outputRow, 13).setValue(content.factual_information_1_question.question || "[Missing Question]");
      sheet.getRange(outputRow, 14).setValue(content.factual_information_1_question.answer || "[Missing Answer]");
      sheet.getRange(outputRow, 15, 1, 3).setValues([content.factual_information_1_question.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 13).setValue("[Missing Factual Information #1 Question]");
    }

     if (content.factual_information_2_question) {
      sheet.getRange(outputRow, 18).setValue(content.factual_information_2_question.question || "[Missing Question]");
      sheet.getRange(outputRow, 19).setValue(content.factual_information_2_question.answer || "[Missing Answer]");
      sheet.getRange(outputRow, 20, 1, 3).setValues([content.factual_information_2_question.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 18).setValue("[Missing Factual Information #2 Question]");
    }

     if (content.negative_factual_information_question) {
      sheet.getRange(outputRow, 23).setValue(content.negative_factual_information_question.question || "[Missing Question]");
      sheet.getRange(outputRow, 24).setValue(content.negative_factual_information_question.answer || "[Missing Answer]");
      sheet.getRange(outputRow, 25, 1, 3).setValues([content.negative_factual_information_question.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 23).setValue("[Missing Negative Factual Information Question]");
    }

     if (content.inference_question) {
      sheet.getRange(outputRow, 28).setValue(content.inference_question.question || "[Missing Question]");
      sheet.getRange(outputRow, 29).setValue(content.inference_question.answer || "[Missing Answer]");
      sheet.getRange(outputRow, 30, 1, 3).setValues([content.inference_question.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 28).setValue("[Missing Inference Question]");
    }

    sheet.getRange(outputRow, 33, 1, 2).setValues([[genre, topic]]);
  } catch (e) {
    Logger.log("Error parsing AI response: " + e.toString());
    sheet.getRange(outputRow, 2).setValue("Error: Could not parse AI response.");
  }

  Logger.log("Passage generation completed for row " + outputRow);
}

// Generate passage using gpt-5-mini
function generatePassageWithAI(topic, genre, outputRow) {
  // 1. Build the base prompt
  let prompt = buildPassagePrompt(topic, genre);

  // 2. Get passage history
  const history = getPassageHistory(outputRow);

  // 3. Augment the prompt with history if available
  if (history.length > 0) {
    const historySection = "Here are the last few passages that were generated. Please generate a new passage with a different sentence structure and style to ensure variety:\n\n" + history.map((p, i) => `Previous Passage ${i + 1}:\n${p}`).join('\n\n');
    prompt = `${prompt}\n\n${historySection}`;
  }

  Logger.log("Final prompt sent to API: " + prompt);

  const payload = {
    model: CONFIG['MODEL'],
    messages: [
      {
        role: "system",
        content: CONFIG['System Prompt'] + "\n\nHere is the JSON schema to follow:\n" + CONFIG['JSON Output Schema']
      },
      {
        role: "user",
        content: prompt
      }
    ],
    temperature: CONFIG['TEMPERATURE'],
    max_completion_tokens: CONFIG['MAX_COMPLETION_TOKENS']
  };

  try {
    Logger.log("Complete API Payload: " + JSON.stringify(payload, null, 2));
    const response = UrlFetchApp.fetch(CONFIG['OPENAI_URL'], {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CONFIG['API_KEY']
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true // Add this to get full error response
    });

    const responseText = response.getContentText();
    Logger.log("Raw API Response: " + responseText);

    const data = JSON.parse(responseText);

    if (data.error) {
      Logger.log("API Error: " + data.error.message);
      return null;
    }

    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      return data.choices[0].message.content.trim();
    } else {
      Logger.log("Unexpected API response structure: " + responseText);
      return null;
    }

  } catch (error) {
    Logger.log("Error generating passage: " + error.toString());
    return null;
  }
}

// Build the detailed prompt for passage generation
function buildPassagePrompt(topic, genre) {
  let prompt = CONFIG['User Prompt Template'] || ''; // Fallback to empty string
  prompt = prompt.replace(/{topic}/g, topic);
  prompt = prompt.replace(/{genre}/g, genre);
  return prompt;
}

// Utility function
function countWords(text) {
  return text.trim().split(/\s+/).length;
}

// Fetches the last 5 passages from the sheet to provide as context.
function getPassageHistory(currentRow) {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    return [];
  }
  const startRow = Math.max(2, currentRow - 5); // Start from row 2 at minimum
  const numRows = currentRow - startRow;

  if (numRows <= 0) {
    return [];
  }

  const range = sheet.getRange(startRow, 2, numRows, 1); // Column B for Passage
  const values = range.getValues();

  // Flatten the 2D array and filter out any empty or non-string values
  return values.flat().filter(passage => typeof passage === 'string' && passage.trim() !== '');
}

// --- Trigger-Based Batch Processing ---

// Starts the batch generation process by setting up a time-driven trigger.
function startBatchProcess() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const batchSize = sheet.getRange('B1').getValue() || 5;

  // Clear any existing triggers to prevent duplicates
  stopBatchProcess();

  // Use PropertiesService to store the state
  const userProperties = PropertiesService.getUserProperties();
  userProperties.setProperty('batchIndex', '0');
  userProperties.setProperty('batchSize', batchSize.toString());

  // Create a trigger to run the processing function every 1 minute
  ScriptApp.newTrigger('processBatchChunk')
    .timeBased()
    .everyMinutes(1)
    .create();

  SpreadsheetApp.getUi().alert('Batch process started. Chunks of up to 10 passages will be generated in the background every minute. You can close this sheet.');
}

// Processes a chunk of up to 10 items from the batch. This function is run by the trigger.
function processBatchChunk() {
  const userProperties = PropertiesService.getUserProperties();
  let index = parseInt(userProperties.getProperty('batchIndex'), 10);
  const size = parseInt(userProperties.getProperty('batchSize'), 10);
  const chunkSize = 10; // Process up to 10 passages per run

  for (let i = 0; i < chunkSize && index < size; i++) {
    // Generate one passage
    generateSinglePassage();

    // Update the index for the next run
    index++;
    userProperties.setProperty('batchIndex', index.toString());
  }

  if (index >= size) {
    // Batch is complete, so stop the process
    stopBatchProcess();
    Logger.log('Batch process completed and trigger has been removed.');
  }
}

// Stops the batch process by deleting the trigger and clearing properties.
function stopBatchProcess() {
  // Delete all triggers for this script
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'processBatchChunk') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }

  // Clear the stored properties
  const userProperties = PropertiesService.getUserProperties();
  userProperties.deleteProperty('batchIndex');
  userProperties.deleteProperty('batchSize');
}


// Wrapper function for single random passage generation from menu
function generateSinglePassage() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Please check your configuration.");
    return;
  }
  const startRow = sheet.getRange('C1').getValue() || 5;
  const nextEmptyRow = Math.max(startRow, sheet.getLastRow() + 1);
  const topic = getTopicFromSheet();
  generateDailyLifeShortPassage(topic, nextEmptyRow);
}

// Get topic based on sheet configuration
function getTopicFromSheet() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Cannot get topic.");
    return "Default Topic";
  }
  const mode = sheet.getRange('A1').getValue();
  const category = sheet.getRange('A2').getValue();
  const specificTopic = sheet.getRange('A3').getValue();

  if (mode === "Specific Topic" && specificTopic) {
    return specificTopic;
  }

  if (mode === "Category Random" && category && TOPICS[category]) {
    const categoryTopics = TOPICS[category];
    return categoryTopics[Math.floor(Math.random() * categoryTopics.length)];
  }

  // Default to "All Random"
  const allTopics = Object.values(TOPICS).flat();
  return allTopics[Math.floor(Math.random() * allTopics.length)];
}

// Menu function to add custom menu item
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('TOEFL Daily Life SHORT')
    .addItem('Generate Single Passage', 'generateSinglePassage')
    .addSeparator()
    .addItem('Start Batch Process', 'startBatchProcess')
    .addItem('Stop Batch Process', 'stopBatchProcess')
    .addToUi();
}

// Helper function to get a sheet by its GID
function getSheetByGid(gid) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const allSheets = ss.getSheets();
  for (let i = 0; i < allSheets.length; i++) {
    if (allSheets[i].getSheetId() == gid) {
      return allSheets[i];
    }
  }
  return null; // Return null if no sheet with the given GID is found
}