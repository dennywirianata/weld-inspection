import gradio as gr
from PIL import Image
import torch
import torchvision.transforms as transforms
from model import RetinaNet  # Import your RetinaNet model definition
import cv2
import numpy as np

# Define the image transformation pipeline
image_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Load the model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = RetinaNet(num_classes=2).to(device)
model.load_state_dict(torch.load("retinanet_best_model.pth", map_location=device))
model.eval()

# Prediction function
def predict_image(image, is_frame):

    if is_frame == "No":
        # Preprocess the image
        img = Image.fromarray(image).convert('RGB')  # Convert Gradio input to PIL Image
        input_tensor = image_transform(img).unsqueeze(0).to(device)

        # Perform inference
        with torch.no_grad():
            prediction = model(input_tensor.float())
            sum_value = abs(torch.sum(prediction[0]))
            p_true = abs(prediction[0][0])
            p_false = abs(prediction[0][1])

        # Interpret the prediction
        if p_true > 0.7:
            result = "Accepted"
            confidence = float(p_true)
        else:
            result = "Rejected"
            confidence = float(p_false)
    else:
        frame = image
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized_frame = cv2.resize(rgb_frame, (224, 224))
        normalized_frame = resized_frame / 255.0
        input_frame = np.expand_dims(normalized_frame, axis=0)

        # Convert to PyTorch tensor and move to device
        input_frame = torch.from_numpy(input_frame).to(device).float()

        # Permute dimensions to [batch_size, channels, height, width]
        input_frame = input_frame.permute(0, 3, 1, 2)

        # Predict using the best model
        with torch.no_grad():
            prediction = model(input_frame)
            sum_value=torch.sum(abs(prediction[0]))
            p_true=abs(prediction[0][0])
            p_false=abs(prediction[0][1])

        if p_true < 0.4:#if p_true > p_false:
            result = "Accepted"
            confidence = float(p_true)
        else:
            result = "Rejected"
            confidence = float(p_false)

    return f"Result: {result}, Confidence: {confidence:.2f}"

# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# RetinaNet Model Prediction")
    with gr.Row():
        image_input = gr.Image(label="Upload Image", type="numpy")
        output_text = gr.Textbox(label="Prediction Result")
    is_frame_radio = gr.Radio(
        choices=["Yes", "No"],  # Options for the radio button
        label="Is this a frame from a video?",  # Label for the radio button
        value="Not a Frame"  # Default selected option
    )
    predict_button = gr.Button("Predict")
    predict_button.click(predict_image, inputs=[image_input, is_frame_radio], outputs=output_text)

# Launch the app
demo.launch()