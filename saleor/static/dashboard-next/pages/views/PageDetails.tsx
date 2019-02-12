import * as React from "react";

import Navigator from "../../components/Navigator";
import PageDetailsPage from "../components/PageDetailsPage";
import { TypedPageDetailsQuery } from "../queries";
import { pageListUrl } from "../urls";

export interface PageDetailsProps {
  id: string;
}

export const PageDetails: React.StatelessComponent<PageDetailsProps> = ({
  id
}) => (
  <Navigator>
    {navigate => (
      <TypedPageDetailsQuery variables={{ id }}>
        {pageDetails => (
          <PageDetailsPage
            disabled={pageDetails.loading}
            saveButtonBarState="default"
            page={pageDetails.data.page}
            onBack={() => navigate(pageListUrl)}
            onRemove={() => undefined}
            onSubmit={() => undefined}
          />
        )}
      </TypedPageDetailsQuery>
    )}
  </Navigator>
);
PageDetails.displayName = "PageDetails";
export default PageDetails;
