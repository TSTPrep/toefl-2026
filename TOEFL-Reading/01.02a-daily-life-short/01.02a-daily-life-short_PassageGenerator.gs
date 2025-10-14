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
  : 'announcement/notice format. Do not begin with the word “notice”. Do not make any heading. Start right with the notice passage consisting of complete sentences.';

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
  const lock = LockService.getUserLock();
  // Try to acquire the lock to prevent concurrent executions. Wait up to 1 second.
  if (!lock.tryLock(1000)) {
    Logger.log('Could not acquire lock, another process is likely running.');
    return;
  }

  try {
    const userProperties = PropertiesService.getUserProperties();
    const indexStr = userProperties.getProperty('batchIndex');
    
    // If the batchIndex property is missing, it means the process was stopped or completed.
    if (!indexStr) {
      Logger.log('Batch process was stopped or completed. Removing trigger.');
      stopBatchProcess(); // Clean up the trigger just in case
      return;
    }

    let index = parseInt(indexStr, 10);
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
  } finally {
    // Always release the lock to allow the next execution to run.
    lock.releaseLock();
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
    .addSeparator()
    .addItem('Start Edit Sheet Conversions', 'startEditSheetConversions')
    .addItem('Delete Editing Sheets', 'deleteEditingSheets') // New menu item
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


/**
 * Duplicates the 'Template' sheet, populates it with data, and creates a hyperlink
 * back to the new sheet in the 'Generated Passages' sheet.
 * If a sheet for a specific row already exists, it is deleted and recreated.
 */
function startEditSheetConversions() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const generateSheet = ss.getSheetByName("Generated Passages");
  const templateSheet = ss.getSheetByName("Template");

  if (!generateSheet) {
    SpreadsheetApp.getUi().alert('Error: "Generated Passages" sheet not found.');
    return;
  }
  if (!templateSheet) {
    SpreadsheetApp.getUi().alert('Error: "Template" sheet not found.');
    return;
  }

  const startRow = generateSheet.getRange('C1').getValue();
  const numRows = generateSheet.getRange('B1').getValue();

  if (!startRow || !numRows || typeof startRow !== 'number' || typeof numRows !== 'number' || startRow <= 1 || numRows <= 0) {
    SpreadsheetApp.getUi().alert('Please enter a valid start row (greater than 1) in C1 and a valid number of rows in B1.');
    return;
  }

  const spreadsheetUrl = ss.getUrl();

  for (let i = 0; i < numRows; i++) {
    const currentRow = startRow + i;
    const newSheetName = "Row " + currentRow;

    const existingSheet = ss.getSheetByName(newSheetName);
    if (existingSheet) {
      ss.deleteSheet(existingSheet);
      Logger.log(`Deleted existing sheet: "${newSheetName}"`);
    }

    const newSheet = templateSheet.copyTo(ss);
    newSheet.setName(newSheetName);
    ss.setActiveSheet(newSheet);

    const sourceData = generateSheet.getRange(currentRow, 1, 1, 32).getValues()[0];
    const topicText = sourceData[0];

    // --- NEW FEATURE: Create Hyperlink ---
    const sheetUrl = '#gid=' + newSheet.getSheetId();
    const linkCell = generateSheet.getRange(currentRow, 1);
    const richTextLink = SpreadsheetApp.newRichTextValue()
      .setText(topicText)
      .setLinkUrl(sheetUrl)
      .build();
    linkCell.setRichTextValue(richTextLink);
    // --- END NEW FEATURE ---


    // --- Populate the new sheet ---
    // Note: We use topicText here instead of sourceData[0] for clarity.
    newSheet.getRange('B3').setValue(topicText);       // Column A -> B3 (Topic)
    newSheet.getRange('B6').setValue(sourceData[1]);   // Column B -> B6 (Passage)
    newSheet.getRange('B9').setValue(sourceData[2]);   // Column C -> B9 (Q1 Question)
    newSheet.getRange('B12').setValue(sourceData[3]);  // Column D -> B12 (Q1 Answer)
    newSheet.getRange('B15:B17').setValues(sourceData.slice(4, 7).map(x => [x])); // E,F,G -> B15:B17

    // --- Question 2 ---
    newSheet.getRange('B20').setValue(sourceData[7]);  // Column H -> B20 (Q2 Question)
    newSheet.getRange('B23').setValue(sourceData[8]);  // Column I -> B23 (Q2 Answer)
    newSheet.getRange('B26:B28').setValues(sourceData.slice(9, 12).map(x => [x])); // J,K,L -> B26:B28

    // --- Question 3 ---
    newSheet.getRange('B31').setValue(sourceData[12]); // Column M -> B31 (Q3 Question)
    newSheet.getRange('B34').setValue(sourceData[13]); // Column N -> B34 (Q3 Answer)
    newSheet.getRange('B37:B39').setValues(sourceData.slice(14, 17).map(x => [x])); // O,P,Q -> B37:B39

    // --- Question 4 ---
    newSheet.getRange('B42').setValue(sourceData[17]); // Column R -> B42 (Q4 Question)
    newSheet.getRange('B45').setValue(sourceData[18]); // Column S -> B45 (Q4 Answer)
    newSheet.getRange('B48:B50').setValues(sourceData.slice(19, 22).map(x => [x])); // T,U,V -> B48:B50

    // --- Question 5 ---
    newSheet.getRange('B53').setValue(sourceData[22]); // Column W -> B53 (Q5 Question)
    newSheet.getRange('B56').setValue(sourceData[23]); // Column X -> B56 (Q5 Answer)
    newSheet.getRange('B59:B61').setValues(sourceData.slice(24, 27).map(x => [x])); // Y,Z,AA -> B59:B61

    // --- Question 6 ---
    newSheet.getRange('B64').setValue(sourceData[27]); // Column AB -> B64 (Q6 Question)
    newSheet.getRange('B67').setValue(sourceData[28]); // Column AC -> B67 (Q6 Answer)
    newSheet.getRange('B70:B72').setValues(sourceData.slice(29, 32).map(x => [x])); // AD,AE,AF -> B70:B72


    Logger.log(`Successfully created and populated sheet: "${newSheetName}" and added link.`);
  }
  SpreadsheetApp.getUi().alert('Sheet conversion process completed!');
}

/**
 * Deletes a range of sheets and removes the corresponding hyperlinks and text formatting
 * in column A of the 'Generated Passages' sheet. The process is based on the start row
 * and number of rows specified in cells C1 and B1.
 */
function deleteEditingSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const generateSheet = ss.getSheetByName("Generated Passages");

  if (!generateSheet) {
    SpreadsheetApp.getUi().alert('Error: "Generated Passages" sheet not found.');
    return;
  }

  // Read the start row from C1 and the amount of rows from B1.
  const startRow = generateSheet.getRange('C1').getValue();
  const numRows = generateSheet.getRange('B1').getValue();

  if (!startRow || !numRows || typeof startRow !== 'number' || typeof numRows !== 'number' || startRow <= 1 || numRows <= 0) {
    SpreadsheetApp.getUi().alert('Please enter a valid start row (greater than 1) in C1 and a valid number of rows in B1.');
    return;
  }

  let deletedCount = 0;
  // Loop through the specified rows to identify sheets and links for deletion.
  for (let i = 0; i < numRows; i++) {
    const currentRow = startRow + i;
    const sheetName = "Row " + currentRow;
    const sheetToDelete = ss.getSheetByName(sheetName);

    // --- FIX: Remove Hyperlink and Clear Formatting ---
    const linkCell = generateSheet.getRange(currentRow, 1);
    const topicText = linkCell.getValue(); // Get the plain text

    // Set the value back to plain text and then clear all formatting.
    // This removes the blue color and underline.
    linkCell.setValue(topicText).clearFormat();
    // --- END FIX ---

    // If the sheet exists, delete it.
    if (sheetToDelete) {
      ss.deleteSheet(sheetToDelete);
      Logger.log(`Deleted sheet: "${sheetName}" and reset its link cell.`);
      deletedCount++;
    } else {
      Logger.log(`Sheet "${sheetName}" not found. Skipping link cell reset.`);
    }
  }

  SpreadsheetApp.getUi().alert(`Deletion process completed. ${deletedCount} sheets were removed and their links were cleared.`);
}

