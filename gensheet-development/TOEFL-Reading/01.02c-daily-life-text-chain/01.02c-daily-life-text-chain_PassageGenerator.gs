// TOEFL 2026 - Reading Section - Daily Life TEXT CHAIN - Passage Generator
// This script generates text chain passages and questions for TOEFL practice exercises.

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
    'Passage Word Count Min': 120,
    'Passage Word Count Max': 200,
    'Genre Distribution Announcements': 0.3, // Keeping these, but system prompt will guide to chat log
    'Genre Distribution Emails': 0.7,     // Keeping these, but system prompt will guide to chat log
    'Gist Purpose Question %': 0.2, // 20%
    'Gist Content Question %': 0, // Omitted
    'Factual Info Question %': 0.9, // Always at least one, 70% two
    'Negative Factual Info Question %': 0.1, // 10% at most one
    'Inference Question %': 0.9, // 90% at least one, 25% two
    'TARGET_SHEET_GID': '', // Placeholder, user must provide the GID of the target sheet
    'System Prompt': 'You are an expert in creating educational content for TOEFL Reading questions. Your task is to generate a text chain passage and five multiple-choice questions based on a given topic and instructions.\n- The passage must be between 120 and 200 words long (including names repeated).\n- The passage must be structured like a chat log or group text.\n- Each entry must begin with name + timestamp (e.g., "Larissa Velez (10:00 A.M.)").\n- Use short, conversational messages rather than paragraphs.\n- Ensure clarity of Roles: Make sure each participant has a distinct responsibility or contribution.\n- Add embedded Clues for Inference: Add brief callbacks ("We know what happened last time") or clarifications.\n- Maintain Consistency with Real-Life Chats: Keep timestamps close together, use short sentences, but avoid slang.\n- Use multiple speakers (usually 3–5 participants).\n- Ensure order matters: later messages build on earlier ones.\n- Maintain an informal but professional tone (colleagues, classmates, project teams).\n- Emphasize task coordination (who does what, by when, and why) and team collaboration around a shared deadline or project.\n- The questions should test comprehension of the passage.\n- Avoid using "for example" explicitly; just give examples.\n- Avoid big lists in both intact sentences and sentences with missing letters.\n- If applicable, split missing letters across two sentences. The first sentence can have most, and the second can have missing letters only at the beginning.\n- Ensure there are two complete sentences at the end after any missing letter sections.\n- Do not always use an obvious "xxx is yyy" opening.\n- Avoid overly technical vocabulary. Aim for freshman-level university textbook language that a newcomer would understand. The trickiest word in ETS samples was "cognitive."\n- The second and third sentences should ideally not use proper nouns.\n- Avoid long-winded final sentences.\n- Ensure sentences with missing letters do not contain lists, as this makes it too difficult for students.\n- Introduce more variety in sentence structure beyond the opening sentence.\n- You must output your response in a JSON format that adheres to the provided schema.',
    'User Prompt Template': 'Generate a text chain about "{topic}". It must be between 120 and 200 words. Then, generate five questions with one correct answer and three plausible distractors each. Adhere to the JSON schema provided in the system prompt.',
    'JSON Output Schema': `
{
  "passage": "string",
  "question1": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question2": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question3": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question4": {
    "question": "string",
    "answer": "string",
    "distractors": ["string", "string", "string"]
  },
  "question5": {
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
function generateDailyLifeTextChainPassage(topic, outputRow) {
  const executionId = Utilities.getUuid();
  Logger.log("[" + executionId + "] START: Generating passage for topic: '" + topic + "' at row " + outputRow);
  
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("[" + executionId + "] Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found.");
    return;
  }

  const questionTypes = getQuestionTypes();
  // Genre is not directly used for text chain, but kept for consistency if needed elsewhere
  const genre = 'text chain'; 

  const apiStartTime = new Date();
  Logger.log("[" + executionId + "] Calling AI API at " + apiStartTime.toISOString());
  
  const generatedContent = generatePassageWithAI(topic, genre, questionTypes[0], questionTypes[1], questionTypes[2], questionTypes[3], questionTypes[4]);
  
  const apiEndTime = new Date();
  const apiDuration = (apiEndTime - apiStartTime) / 1000;
  Logger.log("[" + executionId + "] API call completed in " + apiDuration + " seconds");
  Logger.log("[" + executionId + "] AI-generated content for topic '" + topic + "': " + (generatedContent ? generatedContent.substring(0, 100) + "..." : "NULL"));
  
  if (!generatedContent) {
    Logger.log("[" + executionId + "] ERROR: Failed to generate content from AI for topic: " + topic + ". The AI returned a null or empty response.");
    
    // Check if the row already has content - if so, don't overwrite it!
    const existingPassage = sheet.getRange(outputRow, 2).getValue();
    if (existingPassage && existingPassage.length > 0 && !existingPassage.startsWith("Error:") && !existingPassage.startsWith("[Missing")) {
      Logger.log("[" + executionId + "] WARNING: Row " + outputRow + " already has content. Skipping error write to prevent overwriting good data.");
      return;
    }
    
    sheet.getRange(outputRow, 2).setValue("Error: Failed to generate content");
    return;
  }

  // Assuming the AI returns content in a structured format, e.g., JSON string
  try {
    Logger.log("[" + executionId + "] Parsing JSON response...");
    const content = JSON.parse(generatedContent);
    
    Logger.log("[" + executionId + "] Writing to row " + outputRow + "...");
    sheet.getRange(outputRow, 1).setValue(topic);
    sheet.getRange(outputRow, 2).setValue(content.passage || "[Missing Passage]");

    if (content.question1) {
      sheet.getRange(outputRow, 3).setValue(content.question1.question || "[Missing Question 1]");
      sheet.getRange(outputRow, 4).setValue(content.question1.answer || "[Missing Answer 1]");
      sheet.getRange(outputRow, 5, 1, 3).setValues([content.question1.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 3).setValue("[Missing Question 1]");
    }

    if (content.question2) {
      sheet.getRange(outputRow, 8).setValue(content.question2.question || "[Missing Question 2]");
      sheet.getRange(outputRow, 9).setValue(content.question2.answer || "[Missing Answer 2]");
      sheet.getRange(outputRow, 10, 1, 3).setValues([content.question2.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 8).setValue("[Missing Question 2]");
    }

    if (content.question3) {
      sheet.getRange(outputRow, 13).setValue(content.question3.question || "[Missing Question 3]");
      sheet.getRange(outputRow, 14).setValue(content.question3.answer || "[Missing Answer 3]");
      sheet.getRange(outputRow, 15, 1, 3).setValues([content.question3.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 13).setValue("[Missing Question 3]");
    }

    if (content.question4) {
      sheet.getRange(outputRow, 18).setValue(content.question4.question || "[Missing Question 4]");
      sheet.getRange(outputRow, 19).setValue(content.question4.answer || "[Missing Answer 4]");
      sheet.getRange(outputRow, 20, 1, 3).setValues([content.question4.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 18).setValue("[Missing Question 4]");
    }

    if (content.question5) {
      sheet.getRange(outputRow, 23).setValue(content.question5.question || "[Missing Question 5]");
      sheet.getRange(outputRow, 24).setValue(content.question5.answer || "[Missing Answer 5]");
      sheet.getRange(outputRow, 25, 1, 3).setValues([content.question5.distractors || ["[Missing]", "[Missing]", "[Missing]"]]);
    } else {
      sheet.getRange(outputRow, 23).setValue("[Missing Question 5]");
    }

  } catch (e) {
    Logger.log("[" + executionId + "] ERROR parsing AI response: " + e.toString());
    Logger.log("[" + executionId + "] Content that failed to parse: " + generatedContent);
    
    // Check if the row already has content before overwriting
    const existingPassage = sheet.getRange(outputRow, 2).getValue();
    if (existingPassage && existingPassage.length > 0 && !existingPassage.startsWith("Error:") && !existingPassage.startsWith("[Missing")) {
      Logger.log("[" + executionId + "] WARNING: Row " + outputRow + " already has content. Skipping error write to prevent overwriting good data.");
      return;
    }
    
    sheet.getRange(outputRow, 2).setValue("Error: Could not parse AI response.");
  }

  const totalEndTime = new Date();
  Logger.log("[" + executionId + "] COMPLETE: Passage generation completed for row " + outputRow);
}

// Generate passage using gpt-5-mini with retry logic
function generatePassageWithAI(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type) {
  const maxRetries = 2;
  let lastError = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    if (attempt > 1) {
      Logger.log("Retry attempt " + attempt + " of " + maxRetries + " after waiting 3 seconds...");
      Utilities.sleep(3000); // Wait 3 seconds before retry
    }
    
    try {
      const result = attemptAPICall(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type);
      if (result) {
        if (attempt > 1) {
          Logger.log("SUCCESS on retry attempt " + attempt);
        }
        return result;
      }
      lastError = "API returned null or empty response";
    } catch (error) {
      lastError = error.toString();
      Logger.log("Attempt " + attempt + " failed: " + lastError);
      
      // If it's a timeout or address unavailable error, retry
      if (lastError.includes("Address unavailable") || lastError.includes("timeout")) {
        continue;
      } else {
        // For other errors, don't retry
        Logger.log("Non-retryable error encountered. Stopping retry attempts.");
        break;
      }
    }
  }
  
  Logger.log("All retry attempts failed. Last error: " + lastError);
  return null;
}

// Helper function to make a single API call attempt
function attemptAPICall(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type) {
  const prompt = buildPassagePrompt(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type);

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

  Logger.log("Payload sent to OpenAI API: " + JSON.stringify(payload));

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
}

// Build the detailed prompt for passage generation
function buildPassagePrompt(topic, genre, question1_type, question2_type, question3_type, question4_type, question5_type) {
  let prompt = CONFIG['User Prompt Template'] || ''; // Fallback to empty string
  // Only substitute {topic} as question types are now fixed in the prompt template
  prompt = prompt.replace(/{topic}/g, topic);
  return prompt;
}

function getQuestionTypes() {
  const sheet = getSheetByGid(CONFIG['TARGET_SHEET_GID']);
  if (!sheet) {
    Logger.log("Error: Target sheet with GID " + CONFIG['TARGET_SHEET_GID'] + " not found. Using default question types.");
    return ['Factual Info', 'Factual Info', 'Factual Info', 'Inference', 'Inference'];
  }
  const mode = sheet.getRange('D1').getValue();

  if (mode && mode !== "General Distribution") {
    return [mode, mode, mode, mode, mode];
  }

  // General Distribution Logic
  const questionTypes = [
    { type: 'Gist Purpose', weightConfigKey: 'Gist Purpose Question %' },
    { type: 'Factual Info', weightConfigKey: 'Factual Info Question %' },
    { type: 'Negative Factual Info', weightConfigKey: 'Negative Factual Info Question %' },
    { type: 'Inference', weightConfigKey: 'Inference Question %' }
  ];

  let q1, q2, q3, q4, q5;
  let usedNegativeFactual = false;
  let usedGistPurpose = false;

  // Determine Question 1 (Gist Purpose has a higher chance of being first)
  const rand1 = Math.random();
  if (rand1 < CONFIG['Gist Purpose Question %']) {
    q1 = 'Gist Purpose';
    usedGistPurpose = true;
  } else {
    q1 = getRandomType(questionTypes.filter(t => t.type !== 'Gist Purpose')); // Select from others
  }
  
  if (q1 === 'Negative Factual Info') {
    usedNegativeFactual = true;
  }

  // Determine Question 2
  let availableTypesForQ2 = questionTypes.filter(t => t.type !== 'Gist Content'); // Gist Content is omitted
  
  // Ensure Negative Factual Info appears at most once
  if (usedNegativeFactual) {
    availableTypesForQ2 = availableTypesForQ2.filter(t => t.type !== 'Negative Factual Info');
  }
  
  // Ensure Gist Purpose appears at most once
  if (usedGistPurpose) {
    availableTypesForQ2 = availableTypesForQ2.filter(t => t.type !== 'Gist Purpose');
  }

  q2 = getRandomType(availableTypesForQ2);
  
  if (q2 === 'Negative Factual Info') {
    usedNegativeFactual = true;
  }
  if (q2 === 'Gist Purpose') {
    usedGistPurpose = true;
  }

  // Determine Question 3
  let availableTypesForQ3 = questionTypes.filter(t => t.type !== 'Gist Content');
  
  if (usedNegativeFactual) {
    availableTypesForQ3 = availableTypesForQ3.filter(t => t.type !== 'Negative Factual Info');
  }
  if (usedGistPurpose) {
    availableTypesForQ3 = availableTypesForQ3.filter(t => t.type !== 'Gist Purpose');
  }

  q3 = getRandomType(availableTypesForQ3);
  
  if (q3 === 'Negative Factual Info') {
    usedNegativeFactual = true;
  }
  if (q3 === 'Gist Purpose') {
    usedGistPurpose = true;
  }

  // Determine Question 4
  let availableTypesForQ4 = questionTypes.filter(t => t.type !== 'Gist Content');
  
  if (usedNegativeFactual) {
    availableTypesForQ4 = availableTypesForQ4.filter(t => t.type !== 'Negative Factual Info');
  }
  if (usedGistPurpose) {
    availableTypesForQ4 = availableTypesForQ4.filter(t => t.type !== 'Gist Purpose');
  }

  q4 = getRandomType(availableTypesForQ4);
  
  if (q4 === 'Negative Factual Info') {
    usedNegativeFactual = true;
  }
  if (q4 === 'Gist Purpose') {
    usedGistPurpose = true;
  }

  // Determine Question 5
  let availableTypesForQ5 = questionTypes.filter(t => t.type !== 'Gist Content');
  
  if (usedNegativeFactual) {
    availableTypesForQ5 = availableTypesForQ5.filter(t => t.type !== 'Negative Factual Info');
  }
  if (usedGistPurpose) {
    availableTypesForQ5 = availableTypesForQ5.filter(t => t.type !== 'Gist Purpose');
  }

  q5 = getRandomType(availableTypesForQ5);
  
  return [q1, q2, q3, q4, q5];
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
  Logger.log('Cleaning up any existing triggers before starting...');
  const triggers = ScriptApp.getProjectTriggers();
  let deletedCount = 0;
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'processBatchChunk') {
      ScriptApp.deleteTrigger(triggers[i]);
      deletedCount++;
    }
  }
  Logger.log('Deleted ' + deletedCount + ' existing trigger(s)');
  
  // Use PropertiesService to store the state
  const userProperties = PropertiesService.getUserProperties();
  userProperties.setProperty('batchIndex', '0');
  userProperties.setProperty('batchSize', batchSize.toString());
  
  // Create a trigger to run the processing function every 1 minute
  ScriptApp.newTrigger('processBatchChunk')
      .timeBased()
      .everyMinutes(1)
      .create();
  
  Logger.log('Created new trigger for batch processing');    
  SpreadsheetApp.getUi().alert('Batch process started!\n\n' + 
    (deletedCount > 0 ? 'Cleaned up ' + deletedCount + ' old trigger(s).\n' : '') +
    'Generating ' + batchSize + ' passages total.\n' +
    'Processing up to 3 passages per minute.\n\n' +
    'You can close this sheet and the process will continue in the background.');
}

// Processes a chunk of up to 3 items from the batch. This function is run by the trigger.
function processBatchChunk() {
  const lock = LockService.getScriptLock();
  
  // Try to acquire lock - if another instance is running, skip this execution
  if (!lock.tryLock(1000)) { // Wait up to 1 second for lock
    Logger.log("SKIPPED: Another batch chunk is already running. Exiting to prevent parallel execution.");
    return;
  }
  
  try {
    const chunkStartTime = new Date();
    Logger.log("=== BATCH CHUNK STARTING at " + chunkStartTime.toISOString() + " ===");
    
    const userProperties = PropertiesService.getUserProperties();
    let index = parseInt(userProperties.getProperty('batchIndex'), 10);
    const size = parseInt(userProperties.getProperty('batchSize'), 10);
    const chunkSize = 3; // Process up to 3 passages per run (reduced from 10 to avoid timeouts)
    const maxExecutionTime = 4 * 60 * 1000; // 4 minutes in milliseconds (leave 2 min buffer)

    Logger.log("Batch status: " + index + " of " + size + " completed. Processing up to " + chunkSize + " more.");

    for (let i = 0; i < chunkSize && index < size; i++) {
      // Check if we're approaching the execution time limit
      const elapsedTime = new Date() - chunkStartTime;
      if (elapsedTime > maxExecutionTime) {
        Logger.log("WARNING: Approaching execution time limit (" + (elapsedTime / 1000) + " seconds). Stopping this chunk early.");
        break;
      }
      
      Logger.log("--- Processing item " + (index + 1) + " of " + size + " (elapsed: " + (elapsedTime / 1000) + "s) ---");
      
      // Generate one passage
      try {
        generateSinglePassage();
        
        // Add a small delay between API calls to avoid rate limiting
        if (i < chunkSize - 1 && index < size - 1) {
          Logger.log("Waiting 2 seconds before next generation to avoid rate limiting...");
          Utilities.sleep(2000); // 2 second delay
        }
      } catch (error) {
        Logger.log("ERROR in batch processing item " + (index + 1) + ": " + error.toString());
        // Continue to next item even if this one failed
      }
      
      // Update the index for the next run
      index++;
      userProperties.setProperty('batchIndex', index.toString());
    }
    
    const chunkEndTime = new Date();
    const chunkDuration = (chunkEndTime - chunkStartTime) / 1000;
    Logger.log("=== BATCH CHUNK COMPLETED in " + chunkDuration + " seconds ===");
    
    if (index >= size) {
      // Batch is complete, so stop the process
      stopBatchProcess();
      Logger.log('Batch process completed and trigger has been removed.');
    }
  } finally {
    // Always release the lock
    lock.releaseLock();
  }
}

// Stops the batch process by deleting the trigger and clearing properties.
function stopBatchProcess() {
  // Delete all triggers for this script
  const triggers = ScriptApp.getProjectTriggers();
  let deletedCount = 0;
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'processBatchChunk') {
      ScriptApp.deleteTrigger(triggers[i]);
      deletedCount++;
    }
  }
  
  Logger.log('Deleted ' + deletedCount + ' processBatchChunk trigger(s)');
  
  // Clear the stored properties
  const userProperties = PropertiesService.getUserProperties();
  userProperties.deleteProperty('batchIndex');
  userProperties.deleteProperty('batchSize');
  
  if (deletedCount > 0) {
    SpreadsheetApp.getUi().alert('Batch process stopped. Deleted ' + deletedCount + ' trigger(s).');
  } else {
    SpreadsheetApp.getUi().alert('No batch triggers found to delete.');
  }
}

// EMERGENCY: Force stop ALL triggers and reset everything
function forceStopAllTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  let deletedCount = 0;
  
  Logger.log('Force stopping all triggers...');
  
  for (let i = 0; i < triggers.length; i++) {
    try {
      Logger.log('Deleting trigger: ' + triggers[i].getHandlerFunction());
      ScriptApp.deleteTrigger(triggers[i]);
      deletedCount++;
    } catch (e) {
      Logger.log('Error deleting trigger: ' + e.toString());
    }
  }
  
  // Clear all stored properties
  const userProperties = PropertiesService.getUserProperties();
  userProperties.deleteProperty('batchIndex');
  userProperties.deleteProperty('batchSize');
  
  Logger.log('Force stopped ' + deletedCount + ' trigger(s)');
  SpreadsheetApp.getUi().alert('FORCE STOP COMPLETE: Deleted ALL ' + deletedCount + ' trigger(s) and cleared properties.');
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
  
  Logger.log("generateSinglePassage: Calculated nextEmptyRow = " + nextEmptyRow + " (startRow: " + startRow + ", lastRow: " + sheet.getLastRow() + ")");
  
  const topic = getTopicFromSheet();
  Logger.log("generateSinglePassage: Selected topic = '" + topic + "'");
  
  generateDailyLifeTextChainPassage(topic, nextEmptyRow);
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
  ui.createMenu('TOEFL Daily Life TEXT CHAIN')
    .addItem('Generate Single Passage', 'generateSinglePassage')
    .addSeparator()
    .addItem('Start Batch Process', 'startBatchProcess')
    .addItem('Stop Batch Process', 'stopBatchProcess')
    .addSeparator()
    .addItem('⚠️ FORCE STOP ALL TRIGGERS', 'forceStopAllTriggers')
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
