// TOEFL 2026 - Writing Section - 2-in-1 Passage Generator
// This script generates passages and questions for two different TOEFL Writing exercise types.

// --- GLOBAL CONFIGURATION ---
// Maps the short exercise names to their configuration details.
const EXERCISES = {
  'BuildASentence': {
    sheetName: 'BuildASentence',
    configColumn: 'B'
  },
  'WriteAnEmail': {
    sheetName: 'WriteAnEmail',
    configColumn: 'C'
  }
};

// --- MENU ---
/**
 * Creates the custom menus in the spreadsheet UI when the file is opened.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const exercises = Object.keys(EXERCISES);

  exercises.forEach(exercise => {
    const menu = ui.createMenu(exercise);
    menu.addItem('Generate 1 batch', `generateBatch_${exercise}`);
    menu.addSeparator();
    menu.addItem('Start Batch Process', `startBatchProcess_${exercise}`);
    menu.addItem('Stop Batch Process', 'stopBatchProcess'); // A single stop function is sufficient
    menu.addSeparator();
    menu.addItem('Start Edit Sheet Conversions', `startEditSheetConversions_${exercise}`);
    menu.addItem('Delete Editing Sheets', `deleteEditingSheets_${exercise}`);
    menu.addToUi();
  });
}

// --- MENU WRAPPERS ---
// These small functions connect the menu items to the main logic with the correct exercise name.
function generateBatch_BuildASentence() { generatePassageBatch('BuildASentence'); }
function startBatchProcess_BuildASentence() { startBatchRun('BuildASentence'); }
function startEditSheetConversions_BuildASentence() { startEditSheetConversions('BuildASentence'); }
function deleteEditingSheets_BuildASentence() { deleteEditingSheets('BuildASentence'); }

function generateBatch_WriteAnEmail() { generatePassageBatch('WriteAnEmail'); }
function startBatchProcess_WriteAnEmail() { startBatchRun('WriteAnEmail'); }
function startEditSheetConversions_WriteAnEmail() { startEditSheetConversions('WriteAnEmail'); }
function deleteEditingSheets_WriteAnEmail() { deleteEditingSheets('WriteAnEmail'); }

// --- CONFIGURATION ---
/**
 * Loads the configuration for a specific exercise from the 'Config' sheet.
 * @param {string} exercise The name of the exercise (e.g., 'Choose').
 * @returns {object} The configuration object for the exercise.
 */
function loadConfig(exercise) {
  Logger.log(`Loading configuration for exercise: ${exercise}`);
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const configSheet = ss.getSheetByName('Config');
  if (!configSheet) {
    throw new Error("Configuration sheet named 'Config' not found.");
  }

  const exerciseInfo = EXERCISES[exercise];
  if (!exerciseInfo) {
    throw new Error(`Invalid exercise: ${exercise}`);
  }

  // The column header in the 'Config' sheet should match the exercise key.
  // E.g., The key 'Choose' should map to a column named 'Choose'.
  const data = configSheet.getDataRange().getValues();
  const headers = data[0];
  const colIndex = headers.indexOf(exercise);

  if (colIndex === -1) {
    throw new Error(`Could not find a configuration column named "${exercise}" in the 'Config' sheet.`);
  }

  const config = {};
  for (let i = 1; i < data.length; i++) {
    const key = data[i][0]; // Parameter names in Column A
    let value = data[i][colIndex]; // Values from the exercise's column
    if (key) {
      if (value === "" || value === undefined || value === null) {
        throw new Error(`Missing configuration value for "${key}" in exercise "${exercise}".`);
      }
      config[key] = value;
    }
  }
  Logger.log(`Configuration loaded successfully. Keys: ${Object.keys(config).join(', ')}`);
  return config;
}


// --- TOPICS ---
/**
 * Loads all topics for a specific exercise from the 'Topics' sheet.
 * @param {string} exercise The name of the exercise (e.g., 'Choose').
 * @returns {string[]} An array of topic strings for the specified exercise.
 */
function loadTopics(exercise) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const topicsSheet = ss.getSheetByName('Topics');
  if (!topicsSheet) {
    throw new Error("Topics sheet named 'Topics' not found.");
  }

  const data = topicsSheet.getDataRange().getValues();
  const headers = data[0];
  const targetHeader = `Topic - ${exercise}`;
  const colIndex = headers.indexOf(targetHeader);

  if (colIndex === -1) {
    throw new Error(`Could not find a topic column named "${targetHeader}" in the 'Topics' sheet.`);
  }

  const topics = [];
  // Start from row 1 to skip header
  for (let i = 1; i < data.length; i++) {
    const topic = data[i][colIndex];
    if (topic) { // Only add non-empty cells
      topics.push(topic);
    }
  }
  
  if (topics.length === 0) {
      throw new Error(`No topics found for exercise "${exercise}" under column "${targetHeader}".`);
  }
  
  Logger.log(`Loaded ${topics.length} topics for exercise: ${exercise}`);
  return topics;
}


// --- PASSAGE GENERATION ---
/**
 * Generates a batch of 10 passages for a given exercise.
 * @param {string} exercise The name of the exercise.
 * @param {number|null} [forcedStartRow=null] If provided, forces generation to start at this row.
 */
function generatePassageBatch(exercise, forcedStartRow = null) {
  try {
    Logger.log(`========== Starting generatePassageBatch for exercise: ${exercise} ==========`);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const targetSheetName = EXERCISES[exercise].sheetName;
    const sheet = ss.getSheetByName(targetSheetName);
    if (!sheet) {
      SpreadsheetApp.getUi().alert(`Sheet "${targetSheetName}" not found.`);
      return;
    }

    const config = loadConfig(exercise);
    const topics = loadTopics(exercise);
    
    // 1. Read batch size from config, with validation
    const batchSize = parseInt(config['rows_batch']);
    if (isNaN(batchSize) || batchSize < 5 || batchSize > 20) {
      throw new Error(`Invalid "rows_batch" value for ${exercise}. Please set a number between 5 and 20 in the 'Config' sheet.`);
    }
    
    // 2. Get a random topic for each row in the batch
    const topicsForBatch = [];
    for (let i = 0; i < batchSize; i++) {
      topicsForBatch.push(getTopicFromSheet(sheet, topics));
    }
    Logger.log(`Generated ${batchSize} random topics for the batch.`);
    Logger.log(`Topics for this batch: ${JSON.stringify(topicsForBatch, null, 2)}`);

    // Determine start row
    let startRow;
    if (forcedStartRow) {
      startRow = forcedStartRow;
    } else {
      startRow = sheet.getRange('B1').getValue();
      if (!startRow || startRow === "" || startRow < 2) {
        startRow = sheet.getLastRow() + 1;
        if (startRow < 2) {
            startRow = 2; // Ensure it's at least 2
        }
      }
    }
    
    // Write a placeholder to reserve the rows
    sheet.getRange(startRow, 1, batchSize, 1).setValue('⏳ Generating...');

    Logger.log(`Processing rows: ${startRow} to ${startRow + batchSize - 1}`);
    const generatedContent = generatePassageWithAI(topicsForBatch, config, startRow, batchSize);
    
    // Use a lock only for the final write operation to ensure data integrity
    const lock = LockService.getDocumentLock();
    lock.waitLock(30000);
    try {
      if (!generatedContent) {
        Logger.log(`ERROR: Failed to generate content from AI for rows ${startRow}-${startRow + batchSize - 1}`);
        sheet.getRange(startRow, 2, batchSize, 1).setValue("Error: Failed to generate content from AI.");
        return;
      }

      Logger.log('Parsing AI response as JSON...');
      const contentArray = JSON.parse(generatedContent);
      if (!Array.isArray(contentArray) || contentArray.length !== batchSize) {
          Logger.log(`ERROR: AI response is not a valid array of ${batchSize} items. Got ${contentArray.length} items.`);
          throw new Error(`AI response was not a valid array of ${batchSize} items.`);
      }
      Logger.log(`Successfully parsed JSON array with ${contentArray.length} items`);
      
      // Create an array of arrays for efficient writing to the sheet
      const outputData = contentArray.map((content, index) => {
          const rowData = [
              topicsForBatch[index],       // Column A: Topic
              content.passage || "[N/A]"   // Column B: Passage (or N/A if not provided)
          ];

          // Handle ListenAndRepeat format (passage and array of sentences)
          if (content.sentences && Array.isArray(content.sentences)) {
              rowData.push(...content.sentences);
          } 
          // Handle Interview format (passage and question1, question2, etc.)
          else {
              for (let i = 1; i <= 10; i++) { // Check for up to 10 questions
                  const questionKey = `question${i}`;
                  if (content[questionKey] && typeof content[questionKey] === 'string') {
                      rowData.push(content[questionKey]);
                  }
              }
          }
          return rowData;
      });

      // Write the entire batch
      Logger.log(`Writing data to sheet rows ${startRow} to ${startRow + batchSize - 1}...`);
      sheet.getRange(startRow, 1, batchSize, outputData[0].length).setValues(outputData);
      Logger.log(`✓ Successfully completed batch for rows ${startRow}-${startRow + batchSize - 1}`);
      Logger.log('========== End generatePassageBatch ==========\n');
    } finally {
      lock.releaseLock();
    }

  } catch (e) {
    Logger.log(`========== CRITICAL ERROR in generatePassageBatch for ${exercise} ==========`);
    Logger.log(`Error type: ${e.name}`);
    Logger.log(`Error message: ${e.message}`);
    Logger.log(`Full error: ${e.toString()}`);
    Logger.log(`Stack trace: ${e.stack || 'No stack trace available'}`);
    Logger.log('======================================================================\n');
    SpreadsheetApp.getUi().alert(`An error occurred: ${e.message}`);
  }
}

/**
 * Calls the AI API to generate passages.
 * @param {string[]} topicsForBatch The array of topics for the batch.
 * @param {object} config The configuration object for the exercise.
 * @param {number} startRow The starting row number for this batch.
 * @param {number} batchSize The number of items to generate.
 * @returns {string|null} The AI's response as a JSON string, or null on error.
 */
function generatePassageWithAI(topicsForBatch, config, startRow, batchSize) {
  const prompt = buildPrompt(topicsForBatch, config);
  const fullPrompt = prompt + `\n\nPlease ensure you return a JSON array with exactly ${batchSize} objects. Here is the JSON schema for each object:\n` + config['JSON Output Schema'];

  const provider = (config['provider'] || 'openai').toLowerCase();
  Logger.log(`Using AI Provider: ${provider}`);

  // Log the model being used
  Logger.log(`Using AI Model: ${provider === 'claude' ? config['CLAUDE_MODEL'] : config['MODEL']}`);
  Logger.log(`Temperature: ${config['TEMPERATURE']}, Max Tokens: ${config['MAX_COMPLETION_TOKENS']}`);
  
  // Log the final prompt
  Logger.log('========== FINAL PROMPT SENT TO API ==========');
  Logger.log(fullPrompt);
  Logger.log('==============================================');
  
  let payload;
  let url;
  let headers;

  if (provider === 'claude') {
    url = config['CLAUDE_URL'];
    headers = {
      "Content-Type": "application/json",
      "x-api-key": config['CLAUDE_API_KEY'],
      "anthropic-version": "2023-06-01"
    };
    payload = {
      model: config['CLAUDE_MODEL'],
      messages: [{ role: "user", content: fullPrompt }],
      temperature: parseFloat(config['TEMPERATURE']),
      max_tokens: parseInt(config['MAX_COMPLETION_TOKENS'])
    };
  } else { // Default to openai
    url = config['OPENAI_URL'];
    headers = {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + config['API_KEY']
    };
    payload = {
      model: config['MODEL'],
      messages: [{ role: "user", content: fullPrompt }],
      temperature: parseFloat(config['TEMPERATURE']),
      max_tokens: parseInt(config['MAX_COMPLETION_TOKENS'])
    };
  }

  try {
    Logger.log(`Sending API request for rows ${startRow}-${startRow + batchSize - 1}...`);
    const response = UrlFetchApp.fetch(url, {
      method: "POST",
      headers: headers,
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    
    const responseText = response.getContentText();
    const httpCode = response.getResponseCode();
    
    Logger.log(`API Response HTTP Code: ${httpCode}`);
    Logger.log('========== PURE API RETURN RESULT ==========');
    Logger.log(responseText);
    Logger.log('============================================');
    
    const data = JSON.parse(responseText);

    if (data.error) {
      Logger.log(`API ERROR for rows ${startRow}-${startRow + batchSize - 1}: ${JSON.stringify(data.error)}`);
      throw new Error("API Error: " + data.error.message);
    }

    if (provider === 'claude') {
      if (!data.content || !Array.isArray(data.content) || !data.content[0] || !data.content[0].text) {
        Logger.log(`ERROR: Unexpected Claude API response structure for rows ${startRow}-${startRow + batchSize - 1}`);
        Logger.log(`Response data: ${JSON.stringify(data)}`);
        throw new Error("Unexpected Claude API response structure");
      }
      Logger.log(`Successfully received AI response for rows ${startRow}-${startRow + batchSize - 1}`);
      let content = data.content[0].text.trim();
      // Clean the response if it's wrapped in markdown
      if (content.startsWith("```json")) {
        content = content.substring(7, content.length - 3).trim();
      }
      return content;
    } else { // openai
      if (!data.choices || !data.choices[0] || !data.choices[0].message) {
        Logger.log(`ERROR: Unexpected OpenAI API response structure for rows ${startRow}-${startRow + batchSize - 1}`);
        Logger.log(`Response data: ${JSON.stringify(data)}`);
        throw new Error("Unexpected API response structure");
      }
      Logger.log(`Successfully received AI response for rows ${startRow}-${startRow + batchSize - 1}`);
      return data.choices[0].message.content.trim();
    }
  } catch (error) {
    Logger.log(`========== ERROR calling AI API for rows ${startRow}-${startRow + batchSize - 1} ==========`);
    Logger.log(`Error type: ${error.name}`);
    Logger.log(`Error message: ${error.message}`);
    Logger.log(`Full error: ${error.toString()}`);
    Logger.log(`Stack trace: ${error.stack || 'No stack trace available'}`);
    Logger.log('==================================================================');
    return null;
  }
}

/**
 * Builds the final prompt sent to the AI.
 * @param {string|string[]} topicOrTopics The topic string or an array of topics for generation.
 * @param {object} config The configuration object for the exercise.
 * @returns {string} The complete prompt.
 */
function buildPrompt(topicOrTopics, config) {
  let prompt = config['Prompt'] || '';
  
  if (!prompt.includes('{topic}')) {
    Logger.log("WARNING: The prompt in the 'Config' sheet does not contain the required '{topic}' placeholder. The randomly selected topics will not be injected into the prompt.");
  }

  if (Array.isArray(topicOrTopics)) {
    // Handle multiple topics for a batch
    const topicList = topicOrTopics.map((t, i) => `${i + 1}. ${t}`).join('\n');
    const multiTopicPrompt = `Generate one item for each of the following topics:\n${topicList}`;
    prompt = prompt.replace(/{topic}/g, multiTopicPrompt);
  } else {
    // Handle a single topic
    prompt = prompt.replace(/{topic}/g, `about ${topicOrTopics}`);
  }

  return prompt;
}

// --- BATCH PROCESSING (NEW MODEL) ---

/**
 * Deletes all triggers associated with the batch process.
 */
function deleteTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'executeSingleBatch') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

/**
 * Resets properties and triggers, then starts the first batch execution.
 * This is the main entry point called by the menu.
 * @param {string} exercise The name of the exercise.
 */
function startBatchRun(exercise) {
  // 1. Stop any currently running process completely
  stopBatchProcess(false); // Run silently

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetName = EXERCISES[exercise].sheetName;
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`Sheet "${sheetName}" not found.`);
    return;
  }

  // 2. Read configuration from the sheet
  const numBatches = sheet.getRange("D1").getValue();
  if (!numBatches || typeof numBatches !== 'number' || numBatches < 1) {
    SpreadsheetApp.getUi().alert('Please enter a valid number of batches in cell D1.');
    return;
  }

  let startRow = sheet.getRange('B1').getValue();
  if (!startRow || startRow === "" || startRow < 2) {
    startRow = sheet.getLastRow() + 1;
    if (startRow < 2) startRow = 2;
  }
  
  // 3. Set up the initial state in script properties
  const properties = PropertiesService.getScriptProperties();
  properties.setProperties({
    'batch_exercise': exercise,
    'batches_to_run': numBatches.toString(),
    'batches_completed': '0',
    'next_row_to_use': startRow.toString()
  });

  const config = loadConfig(exercise);
  const batchSize = config['rows_batch'] || 10;
  const totalRows = numBatches * batchSize;

  //SpreadsheetApp.getUi().alert(`Batch process started for ${exercise}. It will run ${numBatches} time(s), generating approximately ${totalRows} rows.`);

  // 4. Kick off the first execution
  executeSingleBatch();
}

/**
 * Processes one batch and sets a trigger for the next one if needed.
 * This function is called by a trigger.
 */
function executeSingleBatch() {
  const properties = PropertiesService.getScriptProperties();
  const state = properties.getProperties();

  const exercise = state.batch_exercise;
  const batchesToRun = parseInt(state.batches_to_run);
  let batchesCompleted = parseInt(state.batches_completed);
  let nextRow = parseInt(state.next_row_to_use);
  
  if (!exercise) {
    Logger.log('Could not find batch exercise in properties. Stopping process.');
    deleteTriggers();
    return;
  }
  
  try {
    // Check if there's work to do
    if (batchesCompleted < batchesToRun) {
      Logger.log(`Processing batch ${batchesCompleted + 1} of ${batchesToRun} for ${exercise}...`);

      // --- CORE LOGIC ---
      generatePassageBatch(exercise, nextRow);
      // ------------------

      // Update state for the next run
      batchesCompleted++;
      const config = loadConfig(exercise);
      const batchSize = parseInt(config['rows_batch']);
      nextRow += batchSize;

      properties.setProperties({
        'batches_completed': batchesCompleted.toString(),
        'next_row_to_use': nextRow.toString()
      });

      // Check again if we're done, and if not, schedule the next run
      if (batchesCompleted < batchesToRun) {
        Logger.log('More batches to process. Setting trigger for next run.');
        ScriptApp.newTrigger('executeSingleBatch')
          .timeBased()
          .after(1000) // Run again in 1 second
          .create();
      } else {
        Logger.log(`All ${batchesToRun} batches completed successfully.`);
        stopBatchProcess(true); // Process finished, stop and show alert
      }
    }
  } catch(e) {
    Logger.log(`An error occurred during executeSingleBatch: ${e.message}`);
    Logger.log(`Stack: ${e.stack}`);
    stopBatchProcess(true); // Stop the process on error and alert the user
  }
}

/**
 * Stops all background batch processes by deleting triggers and properties.
 * @param {boolean} [showAlert=true] Whether to show a confirmation alert.
 */
function stopBatchProcess(showAlert = true) {
  Logger.log('Stopping batch process...');
  deleteTriggers();
  
  const properties = PropertiesService.getScriptProperties();
  properties.deleteProperty('batch_exercise');
  properties.deleteProperty('batches_to_run');
  properties.deleteProperty('batches_completed');
  properties.deleteProperty('next_row_to_use');
  
  if (showAlert) {
    // It's possible this is called from a trigger, so check if UI is available.
    try {
      SpreadsheetApp.getUi().alert('All batch processes have been stopped or completed.');
    } catch (e) {
      Logger.log('Could not show alert because UI is not available (likely run from trigger).');
    }
  }
}

// --- EDITING SHEETS ---
/**
 * Creates individual editing sheets from the main generation sheet.
 * @param {string} exercise The name of the exercise.
 */
function startEditSheetConversions(exercise) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const generateSheetName = EXERCISES[exercise].sheetName;
  const generateSheet = ss.getSheetByName(generateSheetName);
  const templateSheet = ss.getSheetByName("Template");

  if (!generateSheet || !templateSheet) {
    SpreadsheetApp.getUi().alert(`A required sheet ("${generateSheetName}" or "Template") was not found.`);
    return;
  }

  const startRow = generateSheet.getRange('B1').getValue();
  const numRows = generateSheet.getRange('F1').getValue();
  if (!startRow || !numRows || startRow <= 1 || numRows < 1) {
      SpreadsheetApp.getUi().alert('Please enter a valid start row (B1) and number of rows to convert (F1).');
      return;
  }
  const endRow = startRow + numRows - 1;

  for (let i = startRow; i <= endRow; i++) {
    const newSheetName = `${exercise} - Row ${i}`;
    
    let existingSheet = ss.getSheetByName(newSheetName);
    if (existingSheet) {
      ss.deleteSheet(existingSheet);
    }

    const newSheet = templateSheet.copyTo(ss).setName(newSheetName);
    const sourceData = generateSheet.getRange(i, 1, 1, generateSheet.getLastColumn()).getValues()[0];
    
    const topicText = sourceData[0];
    const sheetUrl = '#gid=' + newSheet.getSheetId();
    const richTextLink = SpreadsheetApp.newRichTextValue()
      .setText(topicText)
      .setLinkUrl(sheetUrl)
      .build();
    generateSheet.getRange(i, 1).setRichTextValue(richTextLink);
    
    // This part is highly dependent on your 'Template' sheet's layout.
    // You will need to adjust these cell references to match your template.
    newSheet.getRange('B3').setValue(topicText); 
    newSheet.getRange('B6').setValue(sourceData[1]);
    
    // --- Populate exercise-specific content based on the new template ---
    if (exercise === 'ListenAndRepeat') {
        let sentenceDataIndex = 2; // Sentences start from column C (index 2)
        let targetRow = 9;         // "Text 1" value is in row 9

        // Loop through up to 7 sentences
        for (let j = 0; j < 7; j++) {
            if (sourceData[sentenceDataIndex + j]) {
                newSheet.getRange('B' + targetRow).setValue(sourceData[sentenceDataIndex + j]);
            }
            targetRow += 3; // Move down 3 rows for the next text (skip 2 rows)
        }
    } else if (exercise === 'Interview') {
        let questionDataIndex = 2; // Questions start from column C (index 2)
        let targetRow = 9;         // Assuming "Question 1" value goes in row 9

        // Loop through up to 4 questions, assuming the same template layout
        for (let j = 0; j < 4; j++) {
            if (sourceData[questionDataIndex + j]) {
                newSheet.getRange('B' + targetRow).setValue(sourceData[questionDataIndex + j]);
            }
            targetRow += 3; // Move down 3 rows for the next question
        }
    }
  }
  SpreadsheetApp.getUi().alert(`Sheet conversion process completed for ${exercise}`);
}

/**
 * Deletes individual editing sheets.
 * @param {string} exercise The name of the exercise.
 */
function deleteEditingSheets(exercise) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const generateSheetName = EXERCISES[exercise].sheetName;
    const generateSheet = ss.getSheetByName(generateSheetName);

    if (!generateSheet) {
        SpreadsheetApp.getUi().alert(`Sheet "${generateSheetName}" not found.`);
        return;
    }

    const startRow = generateSheet.getRange('B1').getValue();
    const numRows = generateSheet.getRange('D1').getValue();
    if (!startRow || !numRows || startRow <= 1 || numRows < 1) {
      SpreadsheetApp.getUi().alert('Please enter a valid start row (B1) and number of rows (D1).');
      return;
    }
    const endRow = startRow + numRows - 1;

    for (let i = startRow; i <= endRow; i++) {
        const sheetName = `${exercise} - Row ${i}`;
        const sheetToDelete = ss.getSheetByName(sheetName);
        if (sheetToDelete) {
            ss.deleteSheet(sheetToDelete);
        }
        // Remove the hyperlink from the generation sheet
        const linkCell = generateSheet.getRange(i, 1);
        const topicText = linkCell.getValue();
        linkCell.setValue(topicText).clearFormat();
    }
    SpreadsheetApp.getUi().alert(`Deletion process completed for ${exercise}`);
}


// --- UTILITIES ---
/**
 * Gets a topic based on the settings in A1:A3 of a given sheet.
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet The sheet with the topic settings.
 * @param {string[]} topics The loaded topics array for the current exercise.
 * @returns {string} The selected topic.
 */
function getTopicFromSheet(sheet, topics) {
  const mode = sheet.getRange('A1').getValue();
  const specificTopic = sheet.getRange('A3').getValue();

  if (mode === "Specific Topic" && specificTopic) {
    Logger.log(`Using specific topic from sheet: "${specificTopic}"`);
    return specificTopic;
  }

  // For any other mode ("Category Random", "All Random", or empty),
  // pick a random topic from the list for the current exercise.
  // The category in A2 is ignored as topics are now exercise-specific.
  if (topics.length === 0) {
      throw new Error("No topics available for random selection. Please populate the 'Topics' sheet for this exercise.");
  }
  const randomIndex = Math.floor(Math.random() * topics.length);
  return topics[randomIndex];
}