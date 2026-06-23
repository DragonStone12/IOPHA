import React from 'react';
import { mount } from 'cypress/react';

describe('Component Testing Infrastructure', () => {
  it('mounts a React component', () => {
    const Hello = ({ name }: { name: string }) => <h1>Hello, {name}!</h1>;
    mount(<Hello name="IOPHA" />);
    cy.contains('Hello, IOPHA!').should('be.visible');
  });
});
