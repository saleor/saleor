import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { Menu, MenuItem } from "../..";
import { PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import MenuItemProperties from "../MenuItemProperties";
import MenuItems from "../MenuItems/MenuItems";

interface FormData {
  name: string;
  url: string;
}

interface MenuItemDetailsPageProps extends PageListProps {
  menuItem?: MenuItem & {
    menu: Menu;
  };
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
const MenuItemDetailsPage = decorate<MenuItemDetailsPageProps>(
  ({
    classes,
    disabled,
    menuItem,
    menuItems,
    pageInfo,
    onAdd,
    onBack,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => {
    const initialForm: FormData = {
      name: menuItem ? menuItem.name : "",
      url: menuItem ? menuItem.url : ""
    };
    return (
      <Form initial={initialForm} key={JSON.stringify(menuItem)}>
        {({ data, change, errors, hasChanged, submit }) => (
          <Container width="md">
            <PageHeader
              title={menuItem ? menuItem.name : undefined}
              onBack={onBack}
            />
            <div className={classes.root}>
              <div className={classes.cardContainer}>
                <MenuItemProperties
                  disabled={disabled}
                  menuItem={data}
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
MenuItemDetailsPage.displayName = "MenuDetailsPage";
export default MenuItemDetailsPage;
