import { withStyles } from "@material-ui/core/styles";
import * as classNames from "classnames";
import * as React from "react";

import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import DeleteIcon from "@material-ui/icons/Delete";
import Hr from "../../../components/Hr";

import CardTitle from "../../../components/CardTitle";
import Toggle from "../../../components/Toggle";

import i18n from "../../../i18n";

interface CategoryCreateSubcategoriesProps {
  disabled: boolean;
}

const decorate = withStyles(theme => ({
  inputGrid: {
    display: "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "5fr 8fr 30px",
    marginBottom: "1rem"
  },
  helperText: {
    marginBottom: theme.spacing.unit * 4
  },
  deleteIcon: {
    justifySelf: "center",
    alignSelf: "end"
  },
  addSubCat: {
    padding: "0",
    marginTop: ".5rem"
  },
  root: {
    paddingBottom: "0px",
    "&:last-child": {
      paddingBottom: ".5rem"
    }
  }
}));

export const CategoryCreateSubcategories = decorate<
  CategoryCreateSubcategoriesProps
>(({ classes, disabled }) => {
  return (
    <Toggle>
      {(toggled, { toggle }) => (
        <Card>
          <CardTitle
            title={i18n.t("Subcategories")}
            toolbar={
              <Button
                color={toggled ? "default" : "secondary"}
                variant="flat"
                onClick={toggle}
                disabled={disabled}
              >
                {toggled ? i18n.t("Cancel") : i18n.t("Add subcategory")}
              </Button>
            }
          />
          <CardContent className={classNames({ [classes.root]: toggled })}>
            <Typography
              className={classNames({ [classes.helperText]: toggled })}
            >
              {i18n.t("Add subcategories to help you organize your products")}
            </Typography>
            {toggled && (
              <>
                <div className={classes.inputGrid}>
                  <TextField label={i18n.t("Category Name")} />
                  <TextField label={i18n.t("Category Description")} />
                  <IconButton className={classes.deleteIcon} color="secondary">
                    <DeleteIcon />
                  </IconButton>
                </div>

                <Hr />
                <Button
                  variant="flat"
                  color="secondary"
                  className={classes.addSubCat}
                >
                  {i18n.t("Add subcategory")}
                  <AddIcon />
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Toggle>
  );
});
export default CategoryCreateSubcategories;
