import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import { maybe } from "../../misc";
import MenuDetailsPage from "../components/MenuDetailsPage";
import { MenuDetailsQuery } from "../queries";
import { menuListUrl, menuUrl, MenuUrlQueryParams } from "../urls";

interface MenuDetailsProps {
  id: string;
  params: MenuUrlQueryParams;
}

const MenuDetails: React.FC<MenuDetailsProps> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const closeModal = () =>
    navigate(
      menuUrl(id, {
        ...params,
        action: undefined,
        id: undefined
      }),
      true
    );

  return (
    <MenuDetailsQuery variables={{ id }}>
      {({ data, loading }) => {
        return (
          <>
            <MenuDetailsPage
              disabled={loading}
              menu={maybe(() => data.menu)}
              onBack={() => navigate(menuListUrl())}
              onDelete={() => undefined}
              onSubmit={() => undefined}
              saveButtonState="default"
            />
          </>
        );
      }}
    </MenuDetailsQuery>
  );
};
MenuDetails.displayName = "MenuDetails";

export default MenuDetails;
