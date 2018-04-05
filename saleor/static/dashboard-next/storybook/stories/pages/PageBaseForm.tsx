import { storiesOf } from "@storybook/react";
import { DialogContentText } from "material-ui/Dialog";
import * as React from "react";

import PageBaseForm from "../../../page/components/PageBaseForm";

const page = {
  availableOn: "2018-03-20T16:39:08.850105+00:00",
  content:
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin bibendum et justo sit amet viverra. Maecenas euismod auctor nisi et tincidunt. Maecenas ante urna, aliquet at odio sed, gravida efficitur purus. Morbi ut dapibus ante. Nulla eu neque sit amet odio tincidunt porttitor eu quis purus. Aliquam at diam sit amet turpis varius semper vitae non lectus. Vivamus lectus ligula, molestie eu augue eu, cursus tincidunt sem. Nam ornare egestas tincidunt.",
  isVisible: true,
  slug: "lorem-ipsum-dolor",
  title: "Lorem ipsum"
};

storiesOf("Pages / PageBaseForm", module)
  .add("with initial data", () => <PageBaseForm {...page} />)
  .add("with 'created' property", () => {
    const created = "2018-03-20T16:39:08.850105+00:00";
    return <PageBaseForm {...page} created={created} />;
  })
  .add("with 'errors' property", () => {
    const errors = [
      {
        field: "slug",
        message: "To pole jest wymagane."
      },
      {
        field: "title",
        message: "To pole jest wymagane."
      },
      {
        field: "content",
        message: "To pole jest wymagane."
      }
    ];
    return <PageBaseForm {...page} errors={errors} />;
  });
