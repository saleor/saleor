import * as React from "react";

export const NothingFound: React.FC<{ search: string }> = ({ search }) => (
  <div className="search__products--not-found">
    <p className="u-lead u-lead--bold u-uppercase">
      Sorry, but we couldn’t match any search results for: “{search}”
    </p>
    <p>
      Don’t give up - check the spelling, think of something less specific and
      then use the search bar above.
    </p>
  </div>
);

export default NothingFound;
