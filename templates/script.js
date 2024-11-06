

function openLoadingScreen() {
 var LoadingScreen = document.querySelector('.LoadingScreen');
 LoadingScreen.style.display = 'block';
}

 function closeLoadingScreen() {
    var LoadingScreen = document.querySelector('.LoadingScreen');
    LoadingScreen.style.display = 'none';
}


document.getElementById('showUploadForm').addEventListener('click', function() {
    const uploadForm = document.getElementById('uploadForm');
    uploadForm.style.display = uploadForm.style.display === 'none' ? 'block' : 'none';
});

