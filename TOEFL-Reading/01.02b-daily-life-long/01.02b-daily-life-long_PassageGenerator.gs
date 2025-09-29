// TOEFL 2026 - Reading Section - Daily Life LONG - Passage Generator
// This script generates long passages and questions for TOEFL practice exercises.

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
    'MAX_COMPLETION_TOKENS': 8000,
    'API_KEY': '', // Placeholder, user must provide
    'OPENAI_URL': 'https://api.openai.com/v1/chat/completions',
    'Passage Word Count Min': 130,
    'Passage Word Count Max': 170,
    'Genre Distribution Announcements': 0.1,
    'Genre Distribution Emails': 0.9,
    'Gist Purpose Question %': 0.55, // 50-60%
    'Gist Content Question %': 0, // Omitted
    'Factual Info Question %': 0.9, // 90% at least one, 40-50% two
    'Negative Factual Info Question %': 0.1, // 10% at most one
    'Inference Question %': 0.65, // 60-70%
    'TARGET_SHEET_GID': '', // Placeholder, user must provide the GID of the target sheet
    'System Prompt': 'You are an expert in creating educational content for TOEFL Reading questions. Your task is to generate a long passage and four multiple-choice questions based on a given topic and instructions.\n- The passage must be between 130 and 170 words.\n- The passage must be in the style of a "Daily Life" text, such as an email or announcement, with a formal-but-simple register appropriate for a CEFR B1-B2 level.\n- Use short, direct sentences and everyday vocabulary. Avoid idioms or culturally specific slang.\n- The passage must include a date or time, a specific requirement or condition (e.g., "bring ID," "RSVP by Friday"), and subtle clues that can be used for inference questions.\n- The questions should test comprehension of the passage.\n- Avoid using "for example" explicitly; just give examples.\n- Avoid big lists in both intact sentences and sentences with missing letters.\n- If applicable, split missing letters across two sentences. The first sentence can have most, and the second can have missing letters only at the beginning.\n- Ensure there are two complete sentences at the end after any missing letter sections.\n- Do not always use an obvious “xxx is yyy” opening.\n- Avoid overly technical vocabulary. Aim for freshman-level university textbook language that a newcomer would understand. The trickiest word in ETS samples was "cognitive."\n- The second and third sentences should ideally not use proper nouns.\n- Avoid long-winded final sentences.\n- Ensure sentences with missing letters do not contain lists, as this makes it too difficult for students.\n- Introduce more variety in sentence structure beyond the opening sentence.\n- You must output your response in a JSON format that adheres to the provided schema.',
    'User Prompt Template': 'Generate a long {genre} about "{topic}". It must be between 130 and 170 words. Then, generate one "{question1_type}" question, one "{question2_type}" question, one "{question3_type}" question, and one "{question4_type}" question. Each question must have one correct answer and five plausible distractors. Adhere to the JSON schema provided in the system prompt.',
    'JSON Output Schema': `
{
  "passage": "string",
  "question1": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string", "string", "string"]
  },
  "question2": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string", "string", "string"]
  },
  "question3": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string", "string", "string"]
  },
  "question4": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string", "string", "string"]
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
function generateDailyLifeLongPassage(topic, outputRow) {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found.");
    return;
  }
  Logger.log("Generating passage for topic: " + topic);

  const questionTypes = getQuestionTypes();
  const genre = Math.random() < CONFIG['Genre Distribution Emails'] ? 'email with subject line, greeting and sign-off in this format:\nSubject: <Subject Line>\n<e-mail body>'
  : 'announcement/notice format';

  const generatedContent = generatePassageWithAI(topic, genre, questionTypes[0], questionTypes[1], questionTypes[2], questionTypes[3]);
  if (!generatedContent) {
    sheet.getRange(outputRow, 2).setValue("Error: Failed to generate content");
    return;
  }

  // Assuming the AI returns content in a structured format, e.g., JSON string
  try {
    const content = JSON.parse(generatedContent);
    sheet.getRange(outputRow, 1).setValue(topic);
    sheet.getRange(outputRow, 2).setValue(content.passage || "[Missing Passage]");

    if (content.question1) {
      sheet.getRange(outputRow, 3).setValue(content.question1.question || "[Missing Question 1]");
      sheet.getRange(outputRow, 4).setValue(content.question1.answer || "[Missing Answer 1]");
      sheet.getRange(outputRow, 5, 1, 5).setValues([content.question1.distractors || ["[Missing]", "[Missing]", "[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 3).setValue("[Missing Question 1]");
    }

    if (content.question2) {
      sheet.getRange(outputRow, 10).setValue(content.question2.question || "[Missing Question 2]");
      sheet.getRange(outputRow, 11).setValue(content.question2.answer || "[Missing Answer 2]");
      sheet.getRange(outputRow, 12, 1, 5).setValues([content.question2.distractors || ["[Missing]", "[Missing]", "[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 10).setValue("[Missing Question 2]");
    }

    if (content.question3) {
      sheet.getRange(outputRow, 17).setValue(content.question3.question || "[Missing Question 3]");
      sheet.getRange(outputRow, 18).setValue(content.question3.answer || "[Missing Answer 3]");
      sheet.getRange(outputRow, 19, 1, 5).setValues([content.question3.distractors || ["[Missing]", "[Missing]", "[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 17).setValue("[Missing Question 3]");
    }

    if (content.question4) {
      sheet.getRange(outputRow, 24).setValue(content.question4.question || "[Missing Question 4]");
      sheet.getRange(outputRow, 25).setValue(content.question4.answer || "[Missing Answer 4]");
      sheet.getRange(outputRow, 26, 1, 5).setValues([content.question4.distractors || ["[Missing]", "[Missing]", "[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 24).setValue("[Missing Question 4]");
    }

  } catch (e) {
    Logger.log("Error parsing AI response: " + e.toString());
    sheet.getRange(outputRow, 2).setValue("Error: Could not parse AI response.");
  }

  Logger.log("Passage generation completed for row " + outputRow);
}

// Generate passage using gpt-5-mini
function generatePassageWithAI(topic, genre, question1_type, question2_type, question3_type, question4_type) {
  const prompt = buildPassagePrompt(topic, genre, question1_type, question2_type, question3_type, question4_type);

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
function buildPassagePrompt(topic, genre, question1_type, question2_type, question3_type, question4_type) {
  let prompt = CONFIG['User Prompt Template'] || ''; // Fallback to empty string
  prompt = prompt.replace(/{topic}/g, topic);
  prompt = prompt.replace(/{genre}/g, genre);
  prompt = prompt.replace(/{question1_type}/g, question1_type);
  prompt = prompt.replace(/{question2_type}/g, question2_type);
  prompt = prompt.replace(/{question3_type}/g, question3_type);
  prompt = prompt.replace(/{question4_type}/g, question4_type);
  return prompt;
}

function getQuestionTypes() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Using default question types.");
    return ['Factual Info', 'Factual Info', 'Factual Info', 'Factual Info'];
  }
  const mode = sheet.getRange('D1').getValue();

  if (mode && mode !== "General Distribution") {
    return [mode, mode, mode, mode];
  }

  // General Distribution Logic
  const questionTypes = [
    { type: 'Gist Purpose', weightConfigKey: 'Gist Purpose Question %' },
    { type: 'Factual Info', weightConfigKey: 'Factual Info Question %' },
    { type: 'Negative Factual Info', weightConfigKey: 'Negative Factual Info Question %' },
    { type: 'Inference', weightConfigKey: 'Inference Question %' }
  ];

  let q1, q2, q3, q4;

  // Determine Question 1 (Gist Purpose has a higher chance of being first)
  const rand1 = Math.random();
  if (rand1 < CONFIG['Gist Purpose Question %']) {
    q1 = 'Gist Purpose';
  } else {
    q1 = getRandomType(questionTypes.filter(t => t.type !== 'Gist Purpose')); // Select from others
  }

  // Determine Question 2 and 3, respecting constraints
  let availableTypesForQ2 = questionTypes.filter(t => t.type !== 'Gist Content'); // Gist Content is omitted
  
  // Ensure Negative Factual Info appears at most once
  if (q1 === 'Negative Factual Info') {
    availableTypesForQ2 = availableTypesForQ2.filter(t => t.type !== 'Negative Factual Info');
  }

  q2 = getRandomType(availableTypesForQ2);

  let availableTypesForQ3 = availableTypesForQ2.filter(t => t.type !== q2); // Remove Q2 type from consideration for Q3

  // If Q1 or Q2 is Negative Factual Info, remove it from Q3 options
  if (q1 === 'Negative Factual Info' || q2 === 'Negative Factual Info') {
    availableTypesForQ3 = availableTypesForQ3.filter(t => t.type !== 'Negative Factual Info');
  }
  
  // If Q1 or Q2 is Gist Purpose, remove it from Q3 options
  if (q1 === 'Gist Purpose' || q2 === 'Gist Purpose') {
    availableTypesForQ3 = availableTypesForQ3.filter(t => t.type !== 'Gist Purpose');
  }

  q3 = getRandomType(availableTypesForQ3);
  
  // Determine Question 4
  let availableTypesForQ4 = availableTypesForQ3.filter(t => t.type !== q3);
  if (q1 === 'Negative Factual Info' || q2 === 'Negative Factual Info' || q3 === 'Negative Factual Info') {
    availableTypesForQ4 = availableTypesForQ4.filter(t => t.type !== 'Negative Factual Info');
  }
  if (q1 === 'Gist Purpose' || q2 === 'Gist Purpose' || q3 === 'Gist Purpose') {
    availableTypesForQ4 = availableTypesForQ4.filter(t => t.type !== 'Gist Purpose');
  }

  q4 = getRandomType(availableTypesForQ4);
  
  return [q1, q2, q3, q4];
}

function getRandomType(types) {
    const rand = Math.random();
    let cumulative = 0;

    // Create a weighted list
    const weightedList = types.map(t => ({ type: t.type, weight: CONFIG[t.weightConfigKey] || 0 }));
    const totalWeight = weightedList.reduce((sum, item) => sum + item.weight, 0);

    // Normalize weights and select type
    for (const item of weightedList) {
        cumulative += item.weight / totalWeight;
        if (rand < cumulative) {
            return item.type;
        }
    }
    return weightedList[weightedList.length - 1].type; // Fallback
}


// Utility function
function countWords(text) {
  return text.trim().split(/\s+/).length;
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
  generateDailyLifeLongPassage(topic, nextEmptyRow);
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
  ui.createMenu('TOEFL Daily Life LONG')
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
