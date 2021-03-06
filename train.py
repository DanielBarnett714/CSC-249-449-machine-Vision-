import argparse
import torchvision
import torchvision.transforms as transforms
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optim
from shufflenet2 import ShuffleNet
from mobilenet import MobileNet
#from torchsummary import summary
import time


parser = argparse.ArgumentParser(description='PyTorch Emotion Training')
parser.add_argument('--model', default='ShuffleNet' , help='model: ShuffleNet or MobileNet')
parser.add_argument('--lr', default=0.01, type=float, help='initial learning rate')

args = parser.parse_args()

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

print("device: " + str(device))

model = ShuffleNet()

print("Model: " + args.model)

if args.model == 'MobileNet' :
    model = MobileNet()
    

model.to(device)

print("loading data...")


transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])

trainset = torchvision.datasets.ImageFolder(root='./outputs/train', transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, shuffle=True, batch_size=64)

testset = torchvision.datasets.ImageFolder(root='./outputs/val', transform=transform)
testloader = torch.utils.data.DataLoader(testset, shuffle=True, batch_size=1)

classes = ('anger', 'contempt', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise')

#summary(model, (3,224,224))

criterion = nn.CrossEntropyLoss()

learning_rate = args.lr
    
optimizer = optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9, weight_decay=1e-4)

max_accuracy = 0.0
        
stall_count = 0


for epoch in range(90):  # loop over the dataset multiple times
    
    model.train(True)
    
    print("training data:")
    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        # get the inputs
        inputs, labels = data

        inputs, labels = inputs.to(device), labels.to(device)

        # wrap them in Variable
        inputs, labels = Variable(inputs), Variable(labels)

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if i % 500 == 0:    # print every 2000 mini-batches
            print('[%d, %5d] loss: %.3f' % (epoch, i, running_loss / 100))
            running_loss = 0.0

    print('finished epoch %d' % epoch)
    print('calculating accuracy')

    
    start_time = time.time()


    model.train(False)
    
    correct = 0
    total = 1
    
    class_correct = list(0. for i in range(8))
    class_total = list(1. for i in range(8))
    
    count = 0
    
    for data in testloader:
        count +=1
        image, label = data


        image, label = image.to(device), label.to(device)
        output = model(Variable(image))
        _, predicted = torch.max(output.data, 1)
        total += 1
        class_total[label[0]] +=1

        if (label[0] == predicted[0]):
            correct += 1
            class_correct[predicted[0]] += 1


    elapsed_time = time.time() - start_time
    accuracy = (100 * correct / total)
    print('Accuracy of the network on the test images: %d%%' % accuracy)
    print('Took %d seconds to validate' % elapsed_time)

    for i in range(8):
        print('Accuracy of %9s : %2d%%' % (classes[i], 100 * class_correct[i] / class_total[i]))
    
    
    if accuracy > max_accuracy :
        torch.save(model, args.model + ".pt")
        max_accuracy = accuracy
        stall_count = 0
    else:
        stall_count +=1
        
    if stall_count > 4:
        learning_rate = learning_rate * 0.1
        stall_count = 0
        for param_group in optimizer.param_groups:
            param_group['lr'] = learning_rate
        
