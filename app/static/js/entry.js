const params = new URLSearchParams(window.location.search);
const day = params.get("day");
const month = params.get("month");
const year = params.get("year");

const keyPrefix = `entry-${year}-${month}-${day}`;
const profitKey = `${keyPrefix}-profit`;
const notesKey = `${keyPrefix}-notes`;
const imagesKey = `${keyPrefix}-images`;

const profitInput = document.getElementById("profitInput");
const notesInput = document.getElementById("notesInput");
const imageInput = document.getElementById("imageInput");

const carouselWrapper = document.getElementById("carouselWrapper");
const carouselImage = document.getElementById("carouselImage");
const deleteBtn = document.getElementById("deleteBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const imageCountDisplay = document.getElementById("imageCount");

let imageList = [];
let currentImageIndex = 0;

document.getElementById("dateHeading").textContent = `Enter Profit for ${day}/${month}/${year}`;

// Fetch data from the backend and populate the form
(async () => {
    try {
        const response = await fetch(`/api/entry?day=${day}&month=${month}&year=${year}`);
        if (!response.ok) {
            console.error('Failed to fetch entry data:', response.statusText);
            return;
        }
        const data = await response.json();
        profitInput.value = data.profit || 0;
        notesInput.value = data.notes || '';

        // Populate the image list with URLs from the backend
        if (data.images && data.images.length > 0) {
            imageList = data.images;
            showImage(0);
            carouselWrapper.classList.remove("hidden");
            updateImageCount();
        }
    } catch (error) {
        console.error('Error fetching entry data:', error);
    }
})();

document.getElementById("saveBtn").addEventListener("click", async () => {
    const profit = profitInput.value || 0;
    const notes = notesInput.value || "";
    const date = `${year}-${month}-${day}`; // Format: YYYY-MM-DD

    const formData = new FormData();
    formData.append("date", date);
    formData.append("profit", profit);
    formData.append("notes", notes);

    // Append images to the form data
    for (const image of imageList) {
        const blob = await fetch(image).then(res => res.blob());
        formData.append("images", blob, `image-${Date.now()}.jpg`);
    }

    try {
        const response = await fetch('/entry', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            window.location.href = `/index`;
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to save entry.');
        }
    } catch (error) {
        console.error('Error saving entry:', error);
        alert('An error occurred while saving the entry.');
    }
});

imageInput.addEventListener("change", async (e) => {
    const files = [...e.target.files];
    for (const file of files) {
        if (imageList.length >= 5) {
            alert("Maximum of 5 images allowed.");
            break;
        }
        await readImage(file);
    }
    showImage(currentImageIndex);
    carouselWrapper.classList.remove("hidden");
    e.target.value = "";
});

async function readImage(file) {
    return new Promise((resolve, reject) => {
        if (imageList.length >= 5) {
            alert("You can only upload a maximum of 5 images.");
            return reject();
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            const img = new Image();
            img.onload = function () {
                const canvas = document.createElement("canvas");
                const maxWidth = 1600;
                const maxHeight = 1000;
                let width = img.width;
                let height = img.height;

                const scale = Math.min(maxWidth / width, maxHeight / height, 1);
                width *= scale;
                height *= scale;

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, width, height);

                const compressed = canvas.toDataURL("image/jpeg", 0.6);
                if (compressed.length > 2000000) {
                    alert("Image is still too large after compression. Try cropping it.");
                    return reject();
                }

                imageList.push(compressed);
                updateImageCount();
                resolve();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

function updateImageCount() {
    imageCountDisplay.textContent = `${imageList.length}/5 images uploaded`;
}

function showImage(index) {
    if (imageList.length === 0) return;
    currentImageIndex = index;
    carouselImage.src = imageList[index];
}

prevBtn.onclick = () => {
    if (imageList.length === 0) return;
    currentImageIndex = (currentImageIndex - 1 + imageList.length) % imageList.length;
    showImage(currentImageIndex);
};

nextBtn.onclick = () => {
    if (imageList.length === 0) return;
    currentImageIndex = (currentImageIndex + 1) % imageList.length;
    showImage(currentImageIndex);
};

deleteBtn.onclick = () => {
    imageList.splice(currentImageIndex, 1);
    updateImageCount();
    if (imageList.length === 0) {
        carouselWrapper.classList.add("hidden");
        currentImageIndex = 0;
    } else {
        currentImageIndex = Math.min(currentImageIndex, imageList.length - 1);
        showImage(currentImageIndex);
    }
};

window.addEventListener("paste", async (e) => {
    const items = e.clipboardData.items;
    for (const item of items) {
        if (item.type.indexOf("image") === 0 && imageList.length < 5) {
            const file = item.getAsFile();
            await readImage(file);
        }
    }
    showImage(currentImageIndex);
    carouselWrapper.classList.remove("hidden");
});
