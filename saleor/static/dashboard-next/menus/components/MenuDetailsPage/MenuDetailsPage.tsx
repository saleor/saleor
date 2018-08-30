import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { Menu, MenuItem } from "../..";
import { PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import MenuItems from "../MenuItems/MenuItems";
import MenuProperties from "../MenuProperties/MenuProperties";

interface FormData {
  name: string;
}

interface MenuDetailsPageProps extends PageListProps {
  menu?: Menu;
  menuItems?: Array<
    MenuItem & {
      children: {
        totalCount: number;
      };
    }
  >;
  onBack: () => void;
}

const decorate = withStyles(theme => ({
  cardContainer: {
    marginBottom: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: {
      marginBottom: theme.spacing.unit
    }
  },
  root: {}
}));
const MenuDetailsPage = decorate<MenuDetailsPageProps>(
  ({
    classes,
    disabled,
    menu,
    menuItems,
    pageInfo,
    onAdd,
    onBack,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => {
    const initialForm: FormData = {
      name: menu ? menu.name : ""
    };
    return (
      <Form initial={initialForm} key={JSON.stringify(menu)}>
        {({ data, change, errors, hasChanged, submit }) => (
          <Container width="md">
            <PageHeader title={menu ? menu.name : undefined} onBack={onBack} />
            <div className={classes.root}>
              <div className={classes.cardContainer}>
                <MenuProperties
                  disabled={disabled}
                  menu={data}
                  onChange={change}
                  errors={errors}
                />
              </div>
              <div className={classes.cardContainer}>
                <MenuItems
                  disabled={disabled}
                  menuItems={menuItems}
                  pageInfo={pageInfo}
                  onAdd={onAdd}
                  onNextPage={onNextPage}
                  onPreviousPage={onPreviousPage}
                  onRowClick={onRowClick}
                />
              </div>
            </div>
            <SaveButtonBar
              disabled={!hasChanged}
              onCancel={onBack}
              onSave={submit}
            />
          </Container>
        )}
      </Form>
    );
  }
);
MenuDetailsPage.displayName = "MenuDetailsPage";
export default MenuDetailsPage;
