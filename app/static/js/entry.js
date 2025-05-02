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

if (localStorage.getItem(profitKey)) profitInput.value = localStorage.getItem(profitKey);
if (localStorage.getItem(notesKey)) notesInput.value = localStorage.getItem(notesKey);
if (localStorage.getItem(imagesKey)) {
    imageList = JSON.parse(localStorage.getItem(imagesKey));
    if (imageList.length > 0) {
    showImage(0);
    carouselWrapper.classList.remove("hidden");
    updateImageCount();
    }
}

document.getElementById("saveBtn").addEventListener("click", () => {
    localStorage.setItem(profitKey, profitInput.value || "");
    localStorage.setItem(notesKey, notesInput.value || "");

    try {
    localStorage.setItem(imagesKey, JSON.stringify(imageList));
    } catch (e) {
    alert("Image storage failed. Try removing or shrinking some images.");
    return;
    }

    window.location.href = `/index?month=${month}&year=${year}`;
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
