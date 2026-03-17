// Select all the tags so I can loop through them
const buttons = document.querySelectorAll('.tag-btn');


// Add's the active class to buttons when clicked
buttons.forEach((button) => {
    button.addEventListener("click", () => {
        //then re-add to only selected:
        button.classList.toggle("active");

        // collect all the data-sets (tags) of the selected tags, ready to match with cards
        const selectedTags = [];

        buttons.forEach((button) => {
           if (button.classList.contains("active")) {
            selectedTags.push(button.dataset.tag);
           }
        });
    });

 

/* Learning note:
- when adding classList.add... you only add it to one element. 
- when doing classList.toggle... you change from on or off, like a switch. 
- classList.toggle will add 'active' if not present, or remove it if it already is.
*/