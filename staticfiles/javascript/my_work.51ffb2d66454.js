// Select all the tags so I can loop through them
const buttons = document.querySelectorAll(".tag-btn");
const work_cards = document.querySelectorAll(".work-card");

// Select the element for the search bar
const search_bar = document.getElementById("project_search");


/* == Shared filter function == */

function filterProjects() {
  // Get the search query, make lowercase, remove outer spaces
  const search_query = search_bar.value.toLowerCase().trim();

  // Collect all selected tags except "all"
  const selectedTags = [];

  buttons.forEach((btn) => {
    if (btn.classList.contains("active") && btn.dataset.tag !== "all") {
      selectedTags.push(btn.dataset.tag);
    }
  });

  // Loop through all project cards
  work_cards.forEach((card) => {
    const cardTags = card.dataset.tags.toLowerCase();
    const cardName = card.dataset.name.toLowerCase();

    // Check if card matches search
    const matchesSearch =
      search_query === "" ||
      cardTags.includes(search_query) ||
      cardName.includes(search_query);

    // Check if card matches selected tags
    const matchesTags =
      selectedTags.length === 0 ||
      selectedTags.some((tag) => cardTags.includes(tag));

    // Only show if both search and tags match
    if (matchesSearch && matchesTags) {
      card.style.display = "";
    } else {
      card.style.display = "none";
    }
  });
}


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

      // Then re-add to only selected
      button.classList.toggle("active");
    }

    // If no specific tags are selected, make "All" active again
    const selectedTags = [];

    buttons.forEach((btn) => {
      if (btn.classList.contains("active") && btn.dataset.tag !== "all") {
        selectedTags.push(btn.dataset.tag);
      }
    });

    if (selectedTags.length === 0) {
      buttons.forEach((btn) => {
        if (btn.dataset.tag === "all") {
          btn.classList.add("active");
        }
      });
    }

    // Run the shared filter
    filterProjects();
  });
});


/* == Search bar == */

function search_field() {
  // This listens for input (any keys typed) and matches with tags and titles on cards
  search_bar.addEventListener("input", () => {
    filterProjects();
  });
}

// Call the function so it actually runs
search_field();


/* To do:
- When users type a word, it shows relevant projects.
- when users type a tag, it shows projects with that tag.
- when users type a letter, it starts prompting recommendations.
*/


/* Learning note:
- when adding classList.add... you only add it to one element.
- when doing classList.toggle... you change from on or off, like a switch.
- classList.toggle will add 'active' if not present, or remove it if it already is.
*/