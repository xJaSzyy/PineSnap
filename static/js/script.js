
function openLoadingScreen() {
 var LoadingScreen = document.querySelector('.LoadingScreen');
 document.querySelector('.overlay').classList.add('show');
 document.querySelector('.LoadingScreen').classList.add('show');
 LoadingScreen.style.display = 'block';
}

function closeLoadingScreen() {
    var LoadingScreen = document.querySelector('.LoadingScreen');
    document.querySelector('.overlay').classList.remove('show');
    document.querySelector('.LoadingScreen').classList.remove('show');
    LoadingScreen.style.display = 'none';

   
}

document.getElementById('showUploadForm').addEventListener('click', function() {
    const uploadForm = document.getElementById('uploadForm');
    uploadForm.style.display = uploadForm.style.display === 'none' ? 'block' : 'none';
})

function updateFileLabel(files) {
       const fileLabel = document.getElementById('file-label');
       const fileNames = Array.from(files).map(file => file.name).join(', ');
       fileLabel.textContent = fileNames;
}

function zoomImage(src, shelfId) {
       const zoomedImage = document.getElementById('zoomedImage');
       const zoomedImg = document.getElementById('zoomedImg');
       const shelfInfo = document.getElementById('shelfInfo');
       const deleteButton = document.getElementById('deleteButton');
       zoomedImg.src = src;
       shelfInfo.innerText = `Номер полки: ${shelfId}`;
       deleteButton.setAttribute('onclick', `deleteImage(event, '${shelfId}')`);
       zoomedImage.style.display = 'flex';
}

function closeZoom() {
       const zoomedImage = document.getElementById('zoomedImage');
       zoomedImage.style.display = 'none';
}