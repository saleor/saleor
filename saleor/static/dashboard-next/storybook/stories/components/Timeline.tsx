import { storiesOf } from "@storybook/react";
import * as React from "react";

import Timeline, {
  TimelineNode,
  TimelineNote
} from "../../../components/Timeline";
import Decorator from "../../Decorator";

storiesOf("Generics / Timeline", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Timeline>
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-07T16:58:02+00:00"
        title="Expansion panel 1"
      />
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-07T16:48:02+00:00"
        title="Expansion panel 2"
      />
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-06T16:58:02+00:00"
        title="Expansion panel 3"
      />
    </Timeline>
  ))
  .add("with expansion panels", () => (
    <Timeline>
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-07T16:58:02+00:00"
        title="Expansion panel 1"
      >
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-07T16:48:02+00:00"
        title="Expansion panel 2"
      >
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-06T16:58:02+00:00"
        title="Expansion panel 3"
      >
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
    </Timeline>
  ))
  .add("with order notes", () => (
    <Timeline>
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-07T16:58:02+00:00"
        title="Expansion panel 1"
      >
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
      <TimelineNote
        date="2018-05-07T16:58:02+00:00"
        user={{ email: "admin@example.com" }}
        message="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget."
      />
      <TimelineNote
        date="2018-05-07T16:58:02+00:00"
        user={{ email: "ceo@example.com" }}
        message="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget."
      />
      <TimelineNode
        amount={null}
        email={null}
        emailType={null}
        quantity={null}
        type={null}
        date="2018-05-06T16:58:02+00:00"
        title="Expansion panel 3"
      >
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse
        malesuada lacus ex, sit amet blandit leo lobortis eget.
      </TimelineNode>
    </Timeline>
  ));
