import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer,
    DataCollatorForLanguageModeling
)
import json
import pandas as pd
from datasets import Dataset as HFDataset
import numpy as np
from sklearn.model_selection import train_test_split
import logging
import os
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssistantDataset(Dataset):
    """Custom dataset for assistant training data"""
    
    def __init__(self, conversations, tokenizer, max_length=512):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.conversations)
    
    def __getitem__(self, idx):
        conversation = self.conversations[idx]
        
        # Format: "Human: {user_input}\nAssistant: {assistant_response}"
        formatted_text = f"Human: {conversation['user']}\nAssistant: {conversation['assistant']}"
        
        # Tokenize
        encoding = self.tokenizer(
            formatted_text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()  # For causal LM, labels = input_ids
        }

class ModelTrainer:
    """Complete pipeline for training assistant models"""
    
    def __init__(self, model_name="microsoft/DialoGPT-small", output_dir="./assistant_model"):
        self.model_name = model_name
        self.output_dir = output_dir
        self.tokenizer = None
        self.model = None
        
    def setup_model_and_tokenizer(self):
        """Initialize model and tokenizer"""
        logger.info(f"Loading model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Add padding token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # Resize token embeddings if needed
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        logger.info("Model and tokenizer loaded successfully!")
        
    def create_training_data(self):
        """Create sample training data - replace with your own dataset"""
        
        # Sample conversations for a household assistant
        sample_data = [
            {
                "user": "How do I clean a microwave?",
                "assistant": "To clean a microwave: 1) Fill a microwave-safe bowl with 1 cup water and 2 tbsp white vinegar. 2) Microwave on high for 2-3 minutes until steaming. 3) Let it sit for 2 minutes to loosen grime. 4) Carefully remove the bowl and wipe interior with a damp cloth. 5) Clean the turntable separately with warm soapy water."
            },
            {
                "user": "What's the best way to organize a closet?",
                "assistant": "Here's an effective closet organization method: 1) Empty everything and sort by category (shirts, pants, shoes, etc.). 2) Declutter - donate items you haven't worn in a year. 3) Install shelving or organizers if needed. 4) Arrange by frequency of use - daily items at eye level. 5) Use uniform hangers and fold items consistently. 6) Add labels and maintain the system weekly."
            },
            {
                "user": "How often should I water houseplants?",
                "assistant": "Watering frequency depends on the plant type and environment: 1) Most houseplants need watering when the top inch of soil feels dry. 2) Succulents: every 1-2 weeks. 3) Tropical plants: 1-2 times per week. 4) Check soil moisture with your finger rather than following a strict schedule. 5) Factors affecting frequency: season, humidity, pot size, and plant type. 6) Water thoroughly until it drains from the bottom."
            },
            {
                "user": "Help me plan a weekly meal schedule",
                "assistant": "I'll help you create a balanced weekly meal plan: 1) Start by listing family preferences and dietary restrictions. 2) Plan around your schedule - quick meals on busy days. 3) Include variety: aim for different proteins, vegetables, and cuisines throughout the week. 4) Prep ingredients on Sunday for easier weekday cooking. 5) Keep backup meals for unexpected changes. Would you like me to suggest specific meals or help with grocery planning?"
            },
            {
                "user": "What supplies do I need for basic home maintenance?",
                "assistant": "Essential home maintenance supplies include: **Tools**: Screwdriver set, hammer, adjustable wrench, pliers, level, measuring tape. **Hardware**: Screws, nails, wall anchors, duct tape, electrical tape. **Safety**: Flashlight, batteries, first aid kit, smoke detector batteries. **Cleaning**: All-purpose cleaner, drain cleaner, air filters. **Seasonal**: Caulk for sealing, weatherstripping, furnace filters. Store everything in a labeled toolbox for easy access."
            }
        ]
        
        return sample_data
    
    def prepare_dataset(self, conversations, test_size=0.2):
        """Prepare training and validation datasets"""
        
        # Split data
        train_data, val_data = train_test_split(
            conversations, 
            test_size=test_size, 
            random_state=42
        )
        
        # Create datasets
        train_dataset = AssistantDataset(train_data, self.tokenizer)
        val_dataset = AssistantDataset(val_data, self.tokenizer)
        
        logger.info(f"Training samples: {len(train_dataset)}")
        logger.info(f"Validation samples: {len(val_dataset)}")
        
        return train_dataset, val_dataset
    
    def setup_training_arguments(self):
        """Configure training parameters"""
        
        return TrainingArguments(
            output_dir=self.output_dir,
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=2,
            per_device_eval_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=f"{self.output_dir}/logs",
            logging_steps=10,
            eval_steps=50,
            save_steps=100,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=None,  # Disable wandb/tensorboard for now
            fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
            dataloader_pin_memory=False,
            remove_unused_columns=False,
        )
    
    def train_model(self, train_dataset, val_dataset):
        """Train the model"""
        
        # Setup training arguments
        training_args = self.setup_training_arguments()
        
        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # We're doing causal LM, not masked LM
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Train the model
        logger.info("Starting training...")
        trainer.train()
        
        # Save the model
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        logger.info(f"Model saved to {self.output_dir}")
        
        return trainer
    
    def test_trained_model(self, test_prompts=None):
        """Test the trained model with sample prompts"""
        
        if test_prompts is None:
            test_prompts = [
                "How do I remove stains from carpet?",
                "What's the best way to organize kitchen cabinets?",
                "Help me create a cleaning schedule"
            ]
        
        logger.info("Testing trained model...")
        
        for prompt in test_prompts:
            formatted_prompt = f"Human: {prompt}\nAssistant:"
            
            # Tokenize
            inputs = self.tokenizer.encode(
                formatted_prompt, 
                return_tensors='pt'
            )
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 150,
                    num_return_sequences=1,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            assistant_response = response.split("Assistant:")[-1].strip()
            
            print(f"\n{'='*50}")
            print(f"User: {prompt}")
            print(f"Assistant: {assistant_response}")
            print(f"{'='*50}")

def main():
    """Main training pipeline"""
    
    # Initialize trainer
    trainer = ModelTrainer()
    
    # Setup model and tokenizer
    trainer.setup_model_and_tokenizer()
    
    # Create training data
    conversations = trainer.create_training_data()
    
    # Prepare datasets
    train_dataset, val_dataset = trainer.prepare_dataset(conversations)
    
    # Train the model
    trained_model = trainer.train_model(train_dataset, val_dataset)
    
    # Test the trained model
    trainer.test_trained_model()
    
    print("\n🎉 Training completed! Your model is saved in './assistant_model'")
    print("\n📚 Next steps:")
    print("1. Add more training data for better performance")
    print("2. Experiment with different hyperparameters")
    print("3. Evaluate on larger test sets")
    print("4. Deploy your model for real use")

if __name__ == "__main__":
    main()

# Advanced Features to Add:
"""
1. DATA AUGMENTATION:
   - Paraphrase existing conversations
   - Add variations in response style
   - Include error handling examples

2. EVALUATION METRICS:
   - BLEU scores for response quality
   - Perplexity measurements
   - Human evaluation protocols

3. HYPERPARAMETER TUNING:
   - Learning rate scheduling
   - Batch size optimization
   - Model architecture experiments

4. DEPLOYMENT:
   - Model quantization for speed
   - API endpoint creation
   - Real-time inference optimization
"""
