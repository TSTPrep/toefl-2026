// TOEFL 2026 - Reading Section - Complete the Words - Passage Generator
// This script generates academic passages with blanks for TOEFL practice exercises

// Function to load configuration from the 'Config' sheet
function loadConfig() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Find the sheet by its GID
  const configSheet = ss.getSheets().filter(sheet => sheet.getSheetId() == 188417004)[0];
  
  if (!configSheet) {
    Logger.log("Error: Configuration sheet with GID 188417004 not found. Using default values.");
    // Fallback to a default config object if the sheet is not found
    return {
      MODEL: 'gpt-5-mini',
      TEMPERATURE: 1,
      MAX_COMPLETION_TOKENS: 8000,
      PASSAGE_LENGTH: { MIN: 65, MAX: 75 },
      BLANKS_COUNT: 10,
      API_KEY: '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', // Default key
      OPENAI_URL: 'https://api.openai.com/v1/chat/completions'
    };
  }

  const data = configSheet.getDataRange().getValues();
  const config = {};

  data.forEach(row => {
    const key = row[0];
    let value = row[1];
    
    if (key) { // Process only if the key is not empty
      // Convert numeric strings to numbers
      if (!isNaN(parseFloat(value)) && isFinite(value)) {
        value = Number(value);
      }
      config[key] = value;
    }
  });

  // Reconstruct the nested PASSAGE_LENGTH object from flat keys
  if (config.PASSAGE_LENGTH_MIN && config.PASSAGE_LENGTH_MAX) {
    config.PASSAGE_LENGTH = {
      MIN: config.PASSAGE_LENGTH_MIN,
      MAX: config.PASSAGE_LENGTH_MAX
    };
    delete config.PASSAGE_LENGTH_MIN;
    delete config.PASSAGE_LENGTH_MAX;
  }

  return config;
}

// Load configuration at runtime
const CONFIG = loadConfig();

// Function to load topics from the 'Topics' sheet
function loadTopics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Find the sheet by its GID
  const topicsSheet = ss.getSheets().filter(sheet => sheet.getSheetId() == 350240275)[0];

  if (!topicsSheet) {
    Logger.log("Error: Topics sheet with GID 350240275 not found. Returning empty object.");
    return {};
  }

  const data = topicsSheet.getDataRange().getValues();
  const topics = {};

  // Start from the second row to skip the header
  for (let i = 1; i < data.length; i++) {
    const category = data[i][0];
    const topicsString = data[i][1];
    
    if (category && topicsString) {
      // Use regex to find all quoted strings, then remove the quotes
      const topicsArray = (topicsString.match(/"(.*?)"/g) || []).map(topic => topic.replace(/"/g, ''));
      topics[category] = topicsArray;
    }
  }
  
  return topics;
}

// Load topics at runtime
const TOPICS = loadTopics();

// Main function to generate a passage with blanks, including validation and retries
function generateTOEFL2026Passage(topic, outputRow) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  let passage = null;
  let blankedPassage = null;
  let attempts = 0;
  const maxAttempts = 5; // Allow more attempts for stricter validation

  Logger.log("Generating passage for topic: " + topic);

  // Loop to ensure the final output is valid
  while (attempts < maxAttempts && !passage) {
    attempts++;
    Logger.log(`Overall generation attempt ${attempts} for topic "${topic}"`);
    
    // Generate a passage that passes initial AI validation (word count, no lists)
    const generatedText = generatePassageWithAI(topic);

    if (generatedText) {
      Logger.log("Generated Passage: " + generatedText);
      // Apply blanking and then validate the blank count
      const tempBlankedPassage = applyBlankingLogic(generatedText);
      Logger.log("Result from applyBlankingLogic: " + tempBlankedPassage);
      const blankCount = countBlanks(tempBlankedPassage);

      if (blankCount === CONFIG.BLANKS_COUNT) {
        // If blank count is correct, accept the passage
        passage = generatedText;
        blankedPassage = tempBlankedPassage;
        Logger.log("Validation for blank count passed.");
      } else {
        // If blank count is wrong, log it and the loop will retry
        Logger.log(`Validation Failed: Blank count is ${blankCount}, expected ${CONFIG.BLANKS_COUNT}. Retrying...`);
      }
    }
  }

  if (!passage) {
    // If no valid passage is generated after all attempts, write an error
    sheet.getRange(outputRow, 1).setValue(topic);
    sheet.getRange(outputRow, 2).setValue("Error: Failed to generate a valid passage after " + maxAttempts + " attempts.");
    return;
  }

  // Write results to sheet
  sheet.getRange(outputRow, 1).setValue(topic);
  sheet.getRange(outputRow, 2).setValue(passage);
  sheet.getRange(outputRow, 3).setValue(blankedPassage);
  sheet.getRange(outputRow, 4).setValue(countWords(passage));
  sheet.getRange(outputRow, 5).setValue(countBlanks(blankedPassage));

  Logger.log("Passage generation completed for row " + outputRow);
}

// Generate passage using the selected LLM with validation and retries
function generatePassageWithAI(topic) {
  let passage = null;
  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts && !passage) {
    attempts++;
    Logger.log(`Generating passage... Attempt ${attempts}`);
    const generatedText = callLLM(topic);

    if (generatedText && validatePassage(generatedText)) {
      passage = generatedText;
    } else if (generatedText) {
      Logger.log("Generated passage failed validation. Retrying...");
    } else {
      Logger.log("Failed to generate text from API. Retrying...");
    }
  }

  if (!passage) {
    Logger.log("Failed to generate a valid passage after " + maxAttempts + " attempts.");
    return null;
  }

  return passage;
}

// Helper function to call the appropriate LLM API based on the configuration
function callLLM(topic) {
  const provider = CONFIG.MODEL_PROVIDER;

  if (provider === "OpenAI") {
    return callOpenAI(topic);
  } else if (provider === "Anthropic") {
    return callAnthropic(topic);
  } else if (provider === "Google") {
    return callGoogle(topic);
  } else {
    Logger.log("Error: Invalid model provider specified in Config sheet.");
    return null;
  }
}

// Helper function to call the OpenAI API
function callOpenAI(topic) {
  const prompt = buildPassagePrompt(topic);

  const payload = {
    model: CONFIG.OPENAI_MODEL,
    messages: [
      {
        role: "system",
        content: "You are a curriculum developer creating TOEFL reading practice passages. Generate high-quality academic content that follows the specified requirements exactly."
      },
      {
        role: "user",
        content: prompt
      }
    ],
    temperature: CONFIG.TEMPERATURE,
    max_completion_tokens: CONFIG.MAX_COMPLETION_TOKENS
  };

  try {
    const response = UrlFetchApp.fetch(CONFIG.OPENAI_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CONFIG.API_KEY
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const responseText = response.getContentText();
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
    Logger.log("Error calling OpenAI: " + error.toString());
    return null;
  }
}

// Helper function to call the Anthropic API
function callAnthropic(topic) {
  const prompt = buildPassagePrompt(topic);

  const payload = {
    model: CONFIG.ANTHROPIC_MODEL,
    messages: [
      {
        role: "user",
        content: prompt
      }
    ],
    temperature: CONFIG.TEMPERATURE,
    max_tokens: CONFIG.MAX_COMPLETION_TOKENS
  };

  try {
    const response = UrlFetchApp.fetch(CONFIG.ANTHROPIC_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": CONFIG.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const responseText = response.getContentText();
    const data = JSON.parse(responseText);

    if (data.error) {
      Logger.log("API Error: " + data.error.message);
      return null;
    }

    if (data.content && data.content.length > 0 && data.content[0].text) {
      return data.content[0].text.trim();
    } else {
      Logger.log("Unexpected API response structure: " + responseText);
      return null;
    }

  } catch (error) {
    Logger.log("Error calling Anthropic: " + error.toString());
    return null;
  }
}

// Helper function to call the Google API
function callGoogle(topic) {
  const prompt = buildPassagePrompt(topic);

  const payload = {
    contents: [
      {
        parts: [
          {
            text: prompt
          }
        ]
      }
    ],
    generationConfig: {
      temperature: CONFIG.TEMPERATURE,
      maxOutputTokens: CONFIG.MAX_COMPLETION_TOKENS
    }
  };

  try {
    const response = UrlFetchApp.fetch(`${CONFIG.GOOGLE_URL}${CONFIG.GOOGLE_MODEL}:generateContent?key=${CONFIG.GOOGLE_API_KEY}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const responseText = response.getContentText();
    const data = JSON.parse(responseText);

    if (data.error) {
      Logger.log("API Error: " + data.error.message);
      return null;
    }

    if (data.candidates && data.candidates.length > 0 && data.candidates[0].content.parts[0].text) {
      return data.candidates[0].content.parts[0].text.trim();
    } else {
      Logger.log("Unexpected API response structure: " + responseText);
      return null;
    }

  } catch (error) {
    Logger.log("Error calling Google: " + error.toString());
    return null;
  }
}

// Function to split a passage into sentences using AI
function splitSentencesWithAI(passage) {
  const payload = {
    model: CONFIG.OPENAI_MODEL,
    messages: [
      {
        role: "system",
        content: "You are a sentence splitter. Your task is to split the provided text into sentences. Respond with a JSON array of strings, where each string is a sentence. For example, for the input \"Hello world. How are you?\", you should respond with [\"Hello world.\", \"How are you?\"]. Do not add any explanation."
      },
      {
        role: "user",
        content: passage
      }
    ],
    temperature: 1,
    max_completion_tokens: CONFIG.MAX_COMPLETION_TOKENS
  };

  try {
    const response = UrlFetchApp.fetch(CONFIG.OPENAI_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CONFIG.API_KEY
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const responseText = response.getContentText();
    const data = JSON.parse(responseText);

    if (data.error) {
      Logger.log("API Error in splitSentencesWithAI: " + data.error.message);
      return null;
    }

    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      const content = data.choices[0].message.content.trim();
      try {
        const sentences = JSON.parse(content);
        if (Array.isArray(sentences) && sentences.every(s => typeof s === 'string')) {
          return sentences;
        }
      } catch (e) {
        // If direct parsing fails, try to extract from a markdown block
        const jsonMatch = content.match(/\[.*\]/s);
        if (jsonMatch) {
          try {
            const sentences = JSON.parse(jsonMatch[0]);
            if (Array.isArray(sentences) && sentences.every(s => typeof s === 'string')) {
              return sentences;
            }
          } catch (e2) {
            Logger.log("Could not parse sentences from API response after regex match: " + jsonMatch[0]);
          }
        }
      }
      Logger.log("Could not find a valid JSON array in API response: " + content);
    } else {
      Logger.log("Unexpected API response structure in splitSentencesWithAI: " + responseText);
    }
  } catch (error) {
    Logger.log("Error calling OpenAI in splitSentencesWithAI: " + error.toString());
  }
  return null; // Return null if anything fails
}

// Build the detailed prompt for passage generation
function buildPassagePrompt(topic) {
  // Assemble the prompt from the configuration sheet
  let prompt = `${CONFIG.PROMPT_HEADER}\n\n${CONFIG.PROMPT_REQUIREMENTS}\n\n${CONFIG.PROMPT_CONSTRAINTS}\n\n${CONFIG.PROMPT_FOOTER}`;

  // Dynamically replace placeholders in the prompt
  prompt = prompt.replace(/\$\{topic\}/g, topic);
  prompt = prompt.replace(/\$\{PASSAGE_LENGTH.MIN\}/g, CONFIG.PASSAGE_LENGTH.MIN);
  prompt = prompt.replace(/\$\{PASSAGE_LENGTH.MAX\}/g, CONFIG.PASSAGE_LENGTH.MAX);

  return prompt;
}

// Function to validate the generated passage
function validatePassage(passage) {
  const wordCount = countWords(passage);

  // 1. Check word count
  if (wordCount < CONFIG.PASSAGE_LENGTH.MIN || wordCount > CONFIG.PASSAGE_LENGTH.MAX) {
    Logger.log(`Validation Failed: Word count (${wordCount}) is outside the range of ${CONFIG.PASSAGE_LENGTH.MIN}-${CONFIG.PASSAGE_LENGTH.MAX}.`);
    return false;
  }

  // 2. Check for lists (three or more items separated by commas)
  if (passage.match(/,.*,.*,/)) {
    Logger.log("Validation Failed: Passage appears to contain a list.");
    return false;
  }

  Logger.log("Validation Passed.");
  return true;
}

// Apply blanking logic to the generated passage
function applyBlankingLogic(passage) {
  let sentences = splitSentencesWithAI(passage);
  Logger.log("LLM Sentence Splitting Result: " + JSON.stringify(sentences));
  
  if (!sentences) {
    Logger.log("Warning: Failed to split sentences using AI. Blanking may not be accurate. Falling back to regex.");
    // Fallback to regex if AI fails
    sentences = passage.match(/[^.!?]+[.!?]+/g) || [];
  }

  if (sentences.length < 3) {
    Logger.log("Warning: Passage has fewer than 3 sentences, cannot apply blanking as specified.");
    return passage;
  }

  const firstSentence = sentences.shift();
  const secondSentence = sentences.shift();
  const thirdSentence = sentences.shift();
  const remainingSentences = sentences.join(" ");

  let secondSentenceWords = secondSentence.trim().split(/\s+/);
  let thirdSentenceWords = thirdSentence.trim().split(/\s+/);

  const blanksInSecond = 7;
  const blanksInThird = 3;

  for (let i = 0; i < secondSentenceWords.length && i < blanksInSecond; i++) {
    secondSentenceWords[i] = createBlank(secondSentenceWords[i]);
  }

  for (let i = 0; i < thirdSentenceWords.length && i < blanksInThird; i++) {
    thirdSentenceWords[i] = createBlank(thirdSentenceWords[i]);
  }

  return [
    firstSentence.trim(),
    secondSentenceWords.join(" "),
    thirdSentenceWords.join(" "),
    remainingSentences.trim()
  ].join(" ").trim();
}

// Create a blank from a word (second half deleted)
function createBlank(word) {
  if (word.length < 2) return word;

  const midPoint = Math.ceil(word.length / 2);
  return word.substring(0, midPoint) + "{missing}";
}

// Utility functions
function countWords(text) {
  return text.trim().split(/\s+/).length;
}

function countBlanks(text) {
  return (text.match(/\{missing\}/g) || []).length;
}

// --- Trigger-Based Batch Processing ---

// Starts the batch generation process by setting up a time-driven trigger.
function startBatchProcess() {
  const userProperties = PropertiesService.getUserProperties();
  if (userProperties.getProperty('batchIndex')) {
    SpreadsheetApp.getUi().alert('A batch process is already running. Please wait for it to complete or stop it manually before starting a new one.');
    return;
  }

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const batchSize = sheet.getRange('B1').getValue() || 5;
  
  // Clear any existing triggers to prevent duplicates
  stopBatchProcess(); 
  
  // Use PropertiesService to store the state
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
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const startRow = sheet.getRange('C1').getValue() || 5;
  // This logic ensures that we always start writing from an empty row,
  // respecting the configured start row and any existing data.
  const nextEmptyRow = Math.max(startRow, sheet.getLastRow() + 1);
  const topic = getTopicFromSheet();
  generateTOEFL2026Passage(topic, nextEmptyRow);
}

// Get topic based on sheet configuration
function getTopicFromSheet() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
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
  ui.createMenu('TOEFL 2026 Generator')
    .addItem('Generate Single Passage', 'generateSinglePassage')
    .addSeparator()
    .addItem('Start Batch Process', 'startBatchProcess')
    .addItem('Stop Batch Process', 'stopBatchProcess')
    .addToUi();
}
