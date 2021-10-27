import streamlit as st
import pandas as pd
import os, json

# set current SCRIPT file directory as a working directory
os.chdir( os.path.dirname( os.path.abspath(__file__) ) )
st.set_page_config(layout="wide")
pd.set_option('display.max_rows', None)

def main():
    st.title('[Demo] 제어가능한 문장 생성 기술 연구')

    st.text('본 페이지는 최종 결과물이 아닌 견본입니다.')

    # Applying styles to the buttons
    st.markdown("""<style>
                    .st-eb {
                        background-color:#f63366
                    } </style>""", unsafe_allow_html=True)

    # Select Box for the model
    st.sidebar.image('./fig/logo.png', width=200)

    num_return_sequences = st.sidebar.slider("Number of return sentences", min_value=0, max_value=100, value=100)

    slot_seq_matching = st.sidebar.checkbox('Slot Sequence Matching')
    ending_matching = st.sidebar.checkbox('Ending Matching')


    # vocab 
    intent_label_vocab = load_vocab(os.path.join('./data', "intent.label.vocab")) 
    slot_tag_label_vocab = load_vocab(os.path.join('./data', "slot_tag.label.vocab"))
    slot_value_label_vocab  = load_slot_value_vocab(os.path.join('./data', "slot_value.label.vocab"))

    row3_spacer1, row3_1, row3_spacer2 = st.beta_columns((.2, 7.1, .2))
    with row3_1:
        st.markdown("") 
        see_data = st.beta_expander('You can click here to see the slot tags and slot values lists 👉')
        with see_data:
            df = pd.DataFrame( columns = ['Slot tag', 'Slot value'])
            for key, value in slot_value_label_vocab.items():
                value_str = ', '.join(value)
                df=df.append({'Slot tag' : key, 'Slot value' : value_str} , ignore_index=True)
            st.table(df)
    st.text('')


    st.markdown('### 📃 Template')
    template = st.radio(
        "",
        ('0. [weather.maxtemperature(day.p=내일)][day.p,(있어?|찾아줘.)]', 
        '1. [weather.sunrise(day.p=내일,location=전남)][day.p->location,(언제야?|알고싶네?)]',
        '2. [weather.mintemperature(day.p=모레,location=독도)][day.p->location,(알려줄래요?)]',
        '3. [weather.snowfall(day.p=오늘,location=대전 대덕구)][day.p->location,(말해주겠니?)]',
        '4. [weather.windchill(day.p=*,location=*)][day.p->location,(어떨까?)]',
        '5. [weather.rain(location=*,ti_range.p=*)][location->ti_range.p,(올까?)]', 
        '6. [weather.sunset(day.p=*,location=*)][day.p->location,(알려줘.)]',
        '7. [weather.dust(day.p=오늘)][day.p,(정도야?|심할까?|좋아졌어?|좋아?|알려줘)]',
        '8. [weather.rainfall(day.p=*,location=*)][day.p->location,(오려나?|궁금하네)]',
        '9. [weather.snow(day.p=*,ti_range.p=*)][day.p->ti_range.p,(해주시겠습니까?|알려줘.)]'
        ))

    
    template = template[3:]
    splitted = template.replace("[","").split(']')
    # splitted[0] : semantic grammar, [1] : syntax grammar
    semantic_grammar = splitted[0].replace(')','').split('(')
    intent = semantic_grammar[0]
    slot = semantic_grammar[1]
    syntax_grammar = splitted[1].replace("(","").replace(")", "")
    tag_str = syntax_grammar.split(',')[0]
    ending = syntax_grammar.split(',')[1]
        
    st.text('')
    st.text('')
    # -- semantic control grammar input -- #
    scg = '<p style="color:Blue; font-size: 20px;">Semantic Control Grammar</p>'
    st.markdown(scg, unsafe_allow_html=True)
    row13_spacer1, row13_1, row13_spacer2, row13_2, row13_spacer3 = st.beta_columns((.2, 2.3, .2, 2.3, .2))
    with row13_1:
        intent_option = st.text_area('Enter the intent', intent)
        st.write('intent : ', intent_option)
  
    with row13_2:
        slot_option = st.text_area("Enter the slot tags and values", slot)
        _slot_option = slot_option
        if '*' in slot_option:
            _slot_option = slot_option.replace('*', '\*')
        st.write('slot tags and values : ', _slot_option)

    semantic_control_grammar = '[' + intent_option + '(' + slot_option + ')' + ']'
    # st.text(semantic_control_grammar)

    # -- syntax control grammar input -- #
    scg = '<p style="color:Blue; font-size: 20px;">Syntax Control Grammar</p>'
    st.markdown(scg, unsafe_allow_html=True)
    row13_spacer1, row13_1, row13_spacer2, row13_2, row13_spacer3 = st.beta_columns((.2, 2.3, .2, 2.3, .2))
    with row13_1:
        slot_seq_option = st.text_area('Enter the slot order', tag_str)
        st.write('slot order : ', slot_seq_option)
    with row13_2:
        ending_option = st.text_area("Enter the sentence endings", ending)
        st.write('endings : ', ending_option)

    syntax_control_grammar = '[' + slot_seq_option + ',(' + ending_option + ')' + ']'
    # st.text(syntax_control_grammar)

    grammar = semantic_control_grammar + syntax_control_grammar
    st.text('')
    st.text('Control Grammar : '+ grammar)
    st.text('')
    

    grammar_idx = 0
    data = load_json(os.path.join('./data', "gen.data.json"))
    text_data, grammar_data= [], []
    for item in data:
        text_data.append( item['text'][0] )
        grammar_data.append ( item['grammar'] )
    
    for idx, g in enumerate(grammar_data):
        if g == grammar:
            grammar_idx = idx
    
    df = pd.read_csv(os.path.join('./data', "result.out.csv"), delimiter='\t')

    
    # Search button
    if st.button("Search"):
        # Checking for exceptions
        if not check_exceptions(num_return_sequences):
            # Calling the forward method on click of Generate
            with st.spinner('Progress your text .... '):     
                st.subheader('Answer : '+ text_data[grammar_idx])

                is_exist = df['query'] == grammar
                is_seq_match = df['slot_seq'] == 1.0
                is_ending_match = df['ending'] == 1.0

                if slot_seq_matching:
                    filtered = df[is_exist & is_seq_match]            
                if ending_matching:
                    filtered = df[is_exist & is_ending_match]    
                if slot_seq_matching and ending_matching:
                    filtered = df[is_exist & is_seq_match & is_ending_match]
                else:
                    filtered = df[is_exist]
                filtered.rename(columns = {'text' : '생성 문장'}, inplace = True)
                filtered.rename(columns = {'pred' : 'Intent Prediction'}, inplace = True)
                filtered.reset_index(inplace = True) 
                filtered = filtered[:num_return_sequences]    

                #html_table = filtered[['생성 문장', 'pred', 'slot_count']].to_html(col_space='100px', justify='center') 
                st.table(data=filtered[['생성 문장', 'Intent Prediction']])


def check_exceptions(num_return_sequences):
    # Checking for zero on the num of return sequences
    if num_return_sequences == 0:
        st.error("Please set the number of return sequences to more than one")
        return True
    return False

def load_vocab(fn):
    vocab = []
    with open(fn, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            symbol, _id = line.split('\t')
            vocab.append(symbol)

    #vocab.sort()
    return vocab[1:]

def load_slot_value_vocab(fn):
    vocab = {}
    with open(fn, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            slot_tag, slot_value = line.split('\t')
            slot_value = slot_value.replace('{', '').replace('}', '').replace("'", '')
            slot_value = slot_value.split(',')
            vocab[slot_tag] =  slot_value

    for key, value in vocab.items():
        for idx, v in enumerate(value):
            value[idx] = v.lstrip().rstrip()
        value.sort()

    return vocab 

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data

if __name__ == '__main__':
    main()