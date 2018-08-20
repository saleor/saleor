import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";

storiesOf("Generics / PageHeader", module)
  .add("without title", () => <PageHeader />)
  .add("with title", () => <PageHeader title="Lorem ipsum" />)
  .add("with title and back button", () => (
    <PageHeader title="Lorem ipsum" onBack={() => undefined} />
  ))
  .add("with title icon bar", () => (
    <PageHeader title="Lorem ipsum">
      <IconButton>
        <DeleteIcon />
      </IconButton>
    </PageHeader>
  ))
  .add("with title, back button and icon bar", () => (
    <PageHeader title="Lorem ipsum" onBack={() => undefined}>
      <IconButton>
        <DeleteIcon />
      </IconButton>
    </PageHeader>
  ));
