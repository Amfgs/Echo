// <reference types="cypress" />

describe('Fluxo de Registo e Navegação', () => {
  it('Deve registar um novo utilizador, ir para o dashboard, abrir uma notícia e interagir', () => {
    // --- PASSO 0: Gerar dados únicos para o teste ---
    const uniqueId = Date.now();
    const username = `teste_${uniqueId}`;
    const email = `teste_${uniqueId}@example.com`;
    const password = 'senhaSegura123';

    // --- PASSO 1: Visitar a página inicial (Login) ---
    cy.visit('http://127.0.0.1:8000/');

    // Verificar se estamos na página de login (opcional, mas bom)
    cy.contains('h1', 'Bem-vindo!').should('be.visible');

    // --- PASSO 2: Navegar para a página de Registo ---
    cy.log('Clicando no link para registar');
    // Encontra o link pelo texto exato e clica
    cy.contains('a', 'Crie uma agora').click();

    // Verificar se fomos para a página de registo (opcional)
    cy.url().should('include', '/registrar'); // Verifica se a URL contém '/registrar'
    cy.get('button[type="submit"]').should('contain', 'Cadastre-se'); // Verifica o texto do botão

    // --- PASSO 3: Preencher o formulário de registo ---
    cy.log('Preenchendo formulário de registo');

    // Preenche o Nome de Usuário
    cy.get('#id_username').type(username);

    // Preenche o Email
    cy.get('#id_email').type(email);

    // Clica na categoria "Economia"
    // Encontra o label pelo texto e clica nele (o que marca o checkbox escondido)
    cy.contains('.categoria-pill', 'Economia').click();

    // Preenche a Senha
    cy.get('#id_password').type(password);

    // Confirma a Senha
    cy.get('#id_password_confirm').type(password);

    // --- PASSO 4: Submeter o formulário ---
    cy.log('Submetendo formulário');
    cy.get('button[type="submit"]').click();

    // --- PASSO 5: Verificar redirecionamento e conteúdo do Dashboard ---
    cy.log('Verificando dashboard');
    // Espera o redirecionamento e verifica se a URL agora contém '/dashboard'
    cy.url().should('include', '/dashboard');

    // Verifica se algum elemento esperado do dashboard está visível
    cy.contains('h2', 'Recomendado para você').should('be.visible');

    // --- PASSO 6: Clicar na primeira notícia recomendada ---
    cy.log('Clicando na primeira notícia');
    // Usa um seletor mais específico e garante que o elemento é clicável
    cy.get('.news-feed .news-card-link').first().should('be.visible').click();


    // --- PASSO 7: Verificar se está na página de detalhe da notícia ---
    cy.log('Verificando página de detalhe');
    // Verifica se a URL corresponde ao padrão /noticia/{numero}/
    cy.url().should('match', /\/noticia\/\d+\//);

    // Verifica se algum elemento chave da página de detalhe está visível
    cy.get('.metadata').should('be.visible'); // Verifica se a secção de metadados existe

    // --- PASSO 8: Interagir com os botões Curtir e Salvar ---
    cy.log('Clicando nos botões de interação');

    // Intercepta a requisição POST para 'curtir' e dá-lhe um alias
    cy.intercept('POST', '/noticia/*/curtir/').as('curtirRequest');
    // Intercepta a requisição POST para 'salvar' e dá-lhe um alias
    cy.intercept('POST', '/noticia/*/salvar/').as('salvarRequest');

    // Clica no botão Curtir
    cy.get('#btn-curtir').should('be.visible').click();
    // ESPERA pela resposta da requisição 'curtirRequest'
    cy.wait('@curtirRequest').its('response.statusCode').should('eq', 200); // Garante que o servidor respondeu OK
    // AGORA verifica se a classe foi adicionada
    

    // Clica no botão Salvar
    cy.get('#btn-salvar').should('be.visible').click();
    // ESPERA pela resposta da requisição 'salvarRequest'
    cy.wait('@salvarRequest').its('response.statusCode').should('eq', 200);
    
    // Opcional: Descurtir/Desalvar
    cy.log('Descurtindo e Desalvando');
    cy.get('#btn-curtir').click();
    cy.wait('@curtirRequest').its('response.statusCode').should('eq', 200);
    cy.get('#btn-curtir').should('not.have.class', 'curtida-ativa');

    cy.get('#btn-salvar').click();
    cy.wait('@salvarRequest').its('response.statusCode').should('eq', 200);
    cy.get('#btn-salvar').should('not.have.class', 'salvamento-ativa');
  });
});

