let slideIndex = 1;
showSlides(slideIndex)

function moveSlide(n) {
    slideIndex += n
    showSlides(slideIndex)
}

function showSlides(n) {
    let slides = document.getElementsByClassName("carousel-item") // Collect all div's related.
    // As n hits no. of images, we go back to first.
    if (n > slides.length) {
        slideIndex = 1
        }
    if (n < 1) {
        slideIndex = slides.length;
    }
    //Above, you check if you need to go back or forwards.

    // Below, you loop through slides and only... 
    // ... display the one you're on. 
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none"
    }
    slides[slideIndex - 1].style.display = "flex"
}