import pandas as pd
import re

def get_int_option(allowed=[], prompt='') -> int:
    option_input = input(prompt)

    try:
        option_input = int(option_input)
        if allowed:
            assert option_input in allowed
        return option_input
    except:
        print('OPCAO INVALIDA')
        return None


def search_sticker(stickers: pd.DataFrame, text: str) -> str:
    found = stickers[stickers['code'].str.startswith(text)]
        
    if found.empty:
        return text+' NOT FOUND!'
    
    return found[['code', 'quantity']].to_string()


def get_deltas(stickers_set: list, is_add: bool) -> pd.DataFrame:

    delta_by_sticker = 1 if is_add else -1
    
    deltas_df = pd.DataFrame()
    
    for _stickers in stickers_set:
        stickers = _stickers.replace(' ', '').upper()

        match = re.fullmatch(r'[A-Za-z]{3}\d+', stickers)

        if match:
            df = pd.DataFrame({'prefix': stickers[:3], 'id': stickers[3:],
                               'increment': delta_by_sticker},
                              index=[0])
        else:
            prefix, ids = stickers.replace(',', ' ').split(':')
            assert ids.replace(' ', '').isnumeric()

            prefix = prefix.strip().upper()
            ids = ids.split()

            df = pd.DataFrame({'prefix': prefix, 'id':ids}, index=range(len(ids)))
            df = df.assign(increment=delta_by_sticker)
            
        deltas_df = pd.concat([deltas_df, df], ignore_index=True)
    
    deltas_df['id'] = deltas_df['id'].astype(int)
    deltas_df = deltas_df.groupby(['prefix','id'], as_index=False).sum()
    
    return deltas_df


def add_stickers(current_stickers: pd.DataFrame, stickers_to_add: list) -> pd.DataFrame:
    deltas = get_deltas(stickers_to_add, is_add=True)
    all_stickers = update_stickers(current_stickers, deltas)
    return all_stickers


def remove_stickers(current_stickers: pd.DataFrame, stickers_to_rmv: list) -> pd.DataFrame:
    deltas = get_deltas(stickers_to_rmv, is_add=False)
    all_stickers = update_stickers(current_stickers, deltas)
    return all_stickers


def update_stickers(current: pd.DataFrame, adjust: pd.DataFrame) -> pd.DataFrame:
    complete = current.merge(adjust, on=['prefix', 'id'], how='outer')
    complete['quantity'] = complete['quantity'].fillna(0) + complete['increment'].fillna(0)
    complete['quantity'] = complete['quantity'].astype(int)
    
    complete = complete[complete['quantity'].gt(0)]
    complete = complete[current.columns]
    complete = complete.sort_values(by=['prefix', 'id'], ignore_index=True)
    
    mask = complete['code'].isna()
    complete.loc[mask, 'code'] = complete.loc[mask, ['prefix', 'id']].astype(str).sum(axis=1)
    
    return complete


def get_repeated(stickers: pd.DataFrame) -> str:
    repeated = stickers[stickers['quantity'].gt(1)]    
    text = ''
    
    for prefix in repeated['prefix'].unique():
        mask = repeated['prefix'].eq(prefix)
        text += f'{prefix}: {", ".join(repeated.loc[mask, "id"].astype(str).values)}\n'
        
    return text


def get_stickers_set(prompt: str):
    stickers_set = []
    while True:
        inp_str = input(prompt)

        if not inp_str or inp_str.isspace():
            break

        stickers_set.append(inp_str)
    return stickers_set


def write_to_file(content:str, filename: str, mode: str):
    try:
        fhandler = open(filename, mode)
        fhandler.write(content+'\n')
        fhandler.close()
    except:
        print("ERRO ESCREVENDO NO ARQUIVO:", filename)


def get_missing(stickers: pd.DataFrame) -> str:
    all_stickers = pd.read_csv('all_stickers.csv')
    missing = all_stickers.merge(stickers[['code']], on='code', how='outer', indicator='side')
    missing = missing[missing['side']=='left_only']

    text=''
    for prefix in missing['prefix'].unique():
        mask = missing['prefix'].eq(prefix)
        text += f'{prefix}: {", ".join(missing.loc[mask, "id"].astype(str).values)}\n'
        
    return text


def apply_option(stickers: pd.DataFrame, option: str, saved: bool, stickers_filename: str):
    if option == 'Pesquisar':
        while True:
            str_to_search = input('Pesquisar: ')

            if not str_to_search or str_to_search.isspace():
                break

            result = search_sticker(stickers, str_to_search.upper())
            write_to_file(result, 'searches.txt', 'a')
            print(result)

    elif option == 'Adicionar':
        to_add = get_stickers_set('Adicionar: ')
        if to_add:
            stickers = add_stickers(stickers, to_add)
    
    elif option == 'Remover':
        to_rmv = get_stickers_set('Remover: ')
        if to_rmv:
            stickers = remove_stickers(stickers, to_rmv)

    elif option == 'Exportar Repetidas':
        repeated = get_repeated(stickers)
        write_to_file(repeated, 'repeated.txt', 'w')
        print(repeated)
    
    elif option == 'Exportar Faltantes':
        missing = get_missing(stickers)
        write_to_file(missing, 'missing.txt', 'w')
        print(missing)

    elif option == 'Obter Status':
        print('FUNCAO EM DESENVOLVIMENTO!')
        print(f"ALBUM {round(len(stickers)/670, 2)}% COMPLETO")

    elif option == 'Limpar Pesquisas':
        write_to_file('', 'searches.txt', 'w')

    elif option == 'Salvar':
        stickers.to_csv(stickers_filename, index=False)

    elif option == 'Sair':
        if not saved:
            save = None
            while save is None:
                print('Progresso nao salvo. Salvar antes de sair?')
                save = get_int_option(allowed=[1,2,3], prompt='1: Sim\n2: Nao\n3: Voltar\n> ')

            if save == 3:
                return stickers, 1
            elif save == 1:
                stickers.to_csv(stickers_filename, index=False)

        return stickers, 0

    return stickers, 1

if __name__ == "__main__":

    stickers_filename = 'stickers.csv'
    stickers = pd.read_csv(stickers_filename)
    saved = True

    options = { 1: 'Pesquisar',
                2: 'Adicionar',
                3: 'Remover',
                4: 'Exportar Repetidas',
                5: 'Exportar Faltantes',
                6: 'Obter Status',
                7: 'Limpar Pesquisas',
                8: 'Salvar',
                9: 'Sair' }

    while True:
        print(f"""Opções:{chr(10)}{str(options)[1:-1].replace(', ', chr(10)).replace("'", "")}""")

        option_id = get_int_option(allowed=options.keys(), prompt='> ') 
        if option_id is None:
            continue
        
        # use string option so its possible to change the order
        option = options[option_id]

        stickers, keep = apply_option(stickers, option, saved, stickers_filename)
        if not keep: break

        if option in ['Adicionar', 'Remover']: 
            saved = False
        elif option == 'Salvar':
            saved = True
