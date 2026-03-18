// Select all the tags so I can loop through them
const buttons = document.querySelectorAll(".tag-btn");
const work_cards = document.querySelectorAll(".work-card");

// Select the elements for the search bar
const search_bar = document.getElementById('project_search');


/* == Tag buttons == */

// Add's the active class to buttons when clicked
buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const clickedTag = button.dataset.tag;

    // Handle the "All" button separately
    if (clickedTag === "all") {
      buttons.forEach((btn) => {
        btn.classList.remove("active");
      });

      button.classList.add("active");
    } else {
      // If another tag is clicked, remove active from "All"
      buttons.forEach((btn) => {
        if (btn.dataset.tag === "all") {
          btn.classList.remove("active");
        }
      });

      // then re-add to only selected:
      button.classList.toggle("active");
    }

    // collect all the of the selected tags, ready to match with cards
    const selectedTags = [];

    buttons.forEach((btn) => {
      if (btn.classList.contains("active") && btn.dataset.tag !== "all") {
        selectedTags.push(btn.dataset.tag);
      }
    });

    // If no specific tags are selected, make "All" active again
    if (selectedTags.length === 0) {
      buttons.forEach((btn) => {
        if (btn.dataset.tag === "all") {
          btn.classList.add("active");
        }
      });
    }

    // match selected tags with tags of work cards:
    work_cards.forEach((card) => {
      if (
        selectedTags.length === 0 ||
        selectedTags.some((tag) => card.dataset.tags.includes(tag))
      ) {
        card.style.display = "";
      } else {
        card.style.display = "none";
      }
    });
  });
});


/* == Search bar == */

function search_field() {
  // This listens for input (any keys typed) and matches with tags on cards
  search_bar.addEventListener("input", () => {

    // Takes the value entered into the search bar and converts to lower case and removes outter spaces - not in middle
    const search_query = search_bar.value.toLowerCase().trim();

    console.log(search_query);

  })
}

/* To do:
- When users type a word, it shows relevant projects.
- when users type a tag, it shows projects with that tag.
- when users type a letter, it starts prompting recommendations. */




/* Learning note:
- when adding classList.add... you only add it to one element. 
- when doing classList.toggle... you change from on or off, like a switch. 
- classList.toggle will add 'active' if not present, or remove it if it already is.
*/