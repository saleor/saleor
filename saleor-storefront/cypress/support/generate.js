import faker from "faker";

const userBuilder = () => ({
  email: faker.internet.email(),
  password: faker.internet.password()
});

export { userBuilder };
