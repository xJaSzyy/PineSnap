
function openLoadingScreen() {
    let loadingScreen = document.querySelector('.loading-screen');
    document.querySelector('.overlay').classList.add('show');
    document.querySelector('.loading-screen').classList.add('show');
    loadingScreen.style.display = 'block';
}

function closeLoadingScreen() {
    let loadingScreen = document.querySelector('.loading-screen');
    document.querySelector('.overlay').classList.remove('show');
    document.querySelector('.loading-screen').classList.remove('show');
    loadingScreen.style.display = 'none';
}

document.getElementById('upload-input').addEventListener('click', function() {
    const uploadForm = document.getElementById('upload-form');
    uploadForm.style.display = uploadForm.style.display === 'none' ? 'block' : 'none';
})

function updateFileLabel(files) {
    const fileLabel = document.getElementById('file-label');
    if (files.length > 0) {
        fileLabel.innerHTML = Array.from(files).map(file => file.name).join('<br>');
    } else {
        fileLabel.textContent = 'Нет загружаемых файлов';
    }
}

function validateForm() {
    const fileInput = document.getElementById('upload-input');
    if (fileInput.files.length === 0) {
        alert('Пожалуйста, добавьте файлы для загрузки.');
        return false;
    }
    return true;
}

function zoomImage(src, shelfId) {
    const zoomedImage = document.getElementById('zoom-image');
    const zoomedImg = document.getElementById('zoom-img');
    const shelfInfo = document.getElementById('shelf-info');
    const deleteButton = document.getElementById('delete-button');
    zoomedImg.src = src;
    shelfInfo.innerText = `Номер полки: ${shelfId}`;
    deleteButton.setAttribute('onclick', `deleteImage(event, '${shelfId}')`);
    zoomedImage.style.display = 'flex';
}

function closeZoom() {
    const zoomedImage = document.getElementById('zoom-image');
    zoomedImage.style.display = 'none';
}

function updateImage() {
    let select = document.getElementById("fruits");
    let selectedFileName = select.options[select.selectedIndex].text;
    let selectedFilePath = select.value;
    document.getElementById("selectedFileName").innerText = selectedFileName;
    let img = document.getElementById("fileImage");
    img.src = '/static/' + selectedFilePath;
}

function filterFiles() {
    const showAnnotated = document.getElementById('showAnnotated').checked;
    const select = document.getElementById('fruits');

    for (let i = 0; i < select.options.length; i++) {
        const option = select.options[i];
        const txtValue = option.getAttribute('data-txt');

        if (showAnnotated) {
            if (txtValue !== 'None') {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        } else {
            option.style.display = '';
        }
    }
}

document.getElementById('photoForm').onsubmit = function(event) {
    event.preventDefault();
    const numPhotos = document.getElementById('numPhotos').value;
    const destinationFolder = document.getElementById('destinationFolder').value;

    const formData = new FormData();
    formData.append('num_photos', numPhotos);
    formData.append('destination_folder', destinationFolder);
    console.log(`Количество фотографий: ${numPhotos}`);
    console.log(`Путь к папке назначения: ${destinationFolder}`);

    fetch('/copy_photos', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || data.error);
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
};

document.querySelector('form').addEventListener('submit', function(e) {
    const imgsz = document.getElementById('imgsz').value;
    const epochs = document.getElementById('epochs').value;
    const batch = document.getElementById('batch').value;
    const savePeriod = document.getElementById('save_period').value;

    if (imgsz < 1 || epochs < 1 || batch < 1 || savePeriod < 1) {
        e.preventDefault();
        alert('Все значения должны быть больше 0.');
    }
});

document.getElementById('numPhotos').addEventListener('input', function() {
    const min = parseInt(this.min);
    const max = parseInt(this.max);
    const value = parseInt(this.value);

    if (value < min || value > max) {
        this.setCustomValidity(`Пожалуйста, введите число от ${min} до ${max}.`);
    } else {
        this.setCustomValidity('');
    }
});

function handleFlashMessages(messages) {
    messages.forEach(function(msg) {
        let title = msg.category.charAt(0).toUpperCase() + msg.category.slice(1); 
        let icon = msg.category === 'success' ? 'success' : 'error'; 

        swal({
            title: title,
            text: msg.message,
            icon: icon,
            button: "ОК",
        });
    });
}

function openCreateDataSet() {
    let loadingScreen = document.querySelector('.CreateDataSet');
    document.querySelector('.overlayForCD').classList.add('showForCD');
    document.querySelector('.CreateDataSet').classList.add('showForCD');
    loadingScreen.style.display = 'block';
}
   
function closeCreateDataSet() {
    let loadingScreen = document.querySelector('.CreateDataSet');
    document.querySelector('.overlayForCD').classList.remove('showForCD');
    document.querySelector('.CreateDataSet').classList.remove('showForCD');
    loadingScreen.style.display = 'none';
}

function openScript() {
    let loadingScreen = document.querySelector('.Script');
    document.querySelector('.overlayForScript').classList.add('showForScript');
    document.querySelector('.Script').classList.add('showForScript');
    loadingScreen.style.display = 'block';
}
   
function closeScript() {
    let loadingScreen = document.querySelector('.Script');
    document.querySelector('.overlayForScript').classList.remove('showForScript');
    document.querySelector('.Script').classList.remove('showForScript');
    loadingScreen.style.display = 'none';
}

const trainInput = document.getElementById('trainSize');
const valInput = document.getElementById('valSize');

trainInput.addEventListener('input', function() {
    const trainValue = parseFloat(trainInput.value);
    if (!isNaN(trainValue)) {
        valInput.value = (1 - trainValue).toFixed(2);
    }
});
    
valInput.addEventListener('input', function() {
    const valValue = parseFloat(valInput.value);
    if (!isNaN(valValue)) {
        trainInput.value = (1 - valValue).toFixed(2);
    }
});

$(document).ready(function() {
    $('#photoForm').on('submit', function(event) {
        event.preventDefault(); // Prevent default form submission

        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function(response) {
                if (response.exists) {
                    // Display the message in an alert box
                    alert(response.message);
                    // Ask the user to confirm
                    if (confirm("Продолжить?")) {
                        // If the user confirms, send the form again
                        $.ajax({
                            type: 'POST',
                            url: '/copy_photos', // Same handler
                            data: $(this).serialize(),
                            success: function() {
                                window.location.href = '/'; // Redirect to the main page
                            },
                            error: function(err) {
                                alert('Ошибка: ' + err.responseJSON.error);
                            }
                        });
                    }
                } else {
                    // If the folder doesn't exist, continue with the copy operation
                    window.location.href = '/'; // Redirect to the main page
                }
            },
            error: function(err) {
                alert('Ошибка: ' + err.responseJSON.error);
            }
        });
    });
});

function updateFileCount() {
    const select = document.getElementById('datasets');
    const selectedOptions = Array.from(select.selectedOptions);
    const count = selectedOptions.length;

    console.log(`Количество выбранных файлов: ${count}`);
}